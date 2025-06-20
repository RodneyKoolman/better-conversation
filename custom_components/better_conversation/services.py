import base64
import logging
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector
from homeassistant.helpers.typing import ConfigType
from openai import AsyncOpenAI
from openai._exceptions import OpenAIError
from openai.types.chat.chat_completion_content_part_image_param import (
    ChatCompletionContentPartImageParam,
)

from .const import DOMAIN, SERVICE_QUERY_IMAGE

SERVICE_CLEAR_HISTORY = "clear_history"
SERVICE_GET_HISTORY = "get_history"
SERVICE_REFRESH_PROMPTS = "refresh_prompts"

QUERY_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry"): selector.ConfigEntrySelector(
            {
                "integration": DOMAIN,
            }
        ),
        vol.Required("model", default="gpt-4-vision-preview"): cv.string,
        vol.Required("prompt"): cv.string,
        vol.Required("images"): vol.All(cv.ensure_list, [{"url": cv.string}]),
        vol.Optional("max_tokens", default=300): cv.positive_int,
    }
)

CLEAR_HISTORY_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry"): selector.ConfigEntrySelector(
            {
                "integration": DOMAIN,
            }
        ),
    }
)

GET_HISTORY_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry"): selector.ConfigEntrySelector(
            {
                "integration": DOMAIN,
            }
        ),
    }
)

REFRESH_PROMPTS_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry"): selector.ConfigEntrySelector(
            {
                "integration": DOMAIN,
            }
        ),
    }
)

_LOGGER = logging.getLogger(__package__)


async def async_setup_services(hass: HomeAssistant, config: ConfigType) -> None:
    """Set up services for the extended openai conversation component."""

    async def query_image(call: ServiceCall) -> ServiceResponse:
        """Query an image."""
        try:
            model = call.data["model"]
            images = [
                {"type": "image_url", "image_url": to_image_param(hass, image)}
                for image in call.data["images"]
            ]

            messages = [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": call.data["prompt"]}] + images,
                }
            ]
            _LOGGER.info("Prompt for %s: %s", model, messages)

            response = await AsyncOpenAI(
                api_key=hass.data[DOMAIN][call.data["config_entry"]]["api_key"]
            ).chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=call.data["max_tokens"],
            )
            response_dict = response.model_dump()
            _LOGGER.info("Response %s", response_dict)
        except OpenAIError as err:
            raise HomeAssistantError(f"Error generating image: {err}") from err

        return response_dict

    async def clear_history(call: ServiceCall) -> ServiceResponse:
        """Clear conversation history."""
        try:
            config_entry = call.data["config_entry"]
            agent = hass.data[DOMAIN][config_entry]["agent"]
            await agent.async_clear_history()
            _LOGGER.info("Conversation history cleared")
        except Exception as err:
            raise HomeAssistantError(f"Error clearing history: {err}") from err

        return {"success": True}

    async def get_history(call: ServiceCall) -> ServiceResponse:
        """Get conversation history for debugging."""
        try:
            config_entry = call.data["config_entry"]
            agent = hass.data[DOMAIN][config_entry]["agent"]

            # Return a summary of the conversation history
            history_summary = {}
            for conv_key, messages in agent.history.items():
                history_summary[conv_key] = {
                    "message_count": len(messages),
                    "last_message": messages[-1]["content"] if messages else None,
                    "conversation_id": getattr(agent, "_conversation_mapping", {}).get(
                        conv_key, "unknown"
                    ),
                }

            _LOGGER.info("Retrieved conversation history: %s", history_summary)
        except Exception as err:
            raise HomeAssistantError(f"Error getting history: {err}") from err

        return {"history": history_summary}

    async def refresh_prompts(call: ServiceCall) -> ServiceResponse:
        """Force refresh all system messages in existing conversations."""
        try:
            config_entry = call.data["config_entry"]
            agent = hass.data[DOMAIN][config_entry]["agent"]

            refreshed_count = 0
            exposed_entities = agent.get_exposed_entities()

            # Create a dummy user_input for template rendering
            from homeassistant.components import conversation

            dummy_input = conversation.ConversationInput(
                text="",
                context=None,
                language="en",
                conversation_id=None,
                device_id="refresh_service",
            )

            for conv_key, messages in agent.history.items():
                if messages and messages[0]["role"] == "system":
                    # Force refresh the system message
                    messages[0] = agent._generate_system_message(
                        exposed_entities, dummy_input
                    )
                    refreshed_count += 1

            # Save the updated history
            await agent.async_save_history()

            _LOGGER.info(
                "Refreshed system messages for %d conversations", refreshed_count
            )
        except Exception as err:
            raise HomeAssistantError(f"Error refreshing prompts: {err}") from err

        return {"refreshed_count": refreshed_count}

    hass.services.async_register(
        DOMAIN,
        SERVICE_QUERY_IMAGE,
        query_image,
        schema=QUERY_IMAGE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_HISTORY,
        clear_history,
        schema=CLEAR_HISTORY_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_HISTORY,
        get_history,
        schema=GET_HISTORY_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_PROMPTS,
        refresh_prompts,
        schema=REFRESH_PROMPTS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


def to_image_param(hass: HomeAssistant, image) -> ChatCompletionContentPartImageParam:
    """Convert url to base64 encoded image if local."""
    url = image["url"]

    if urlparse(url).scheme in cv.EXTERNAL_URL_PROTOCOL_SCHEMA_LIST:
        return image

    if not hass.config.is_allowed_path(url):
        raise HomeAssistantError(
            f"Cannot read `{url}`, no access to path; "
            "`allowlist_external_dirs` may need to be adjusted in "
            "`configuration.yaml`"
        )
    if not Path(url).exists():
        raise HomeAssistantError(f"`{url}` does not exist")
    mime_type, _ = mimetypes.guess_type(url)
    if mime_type is None or not mime_type.startswith("image"):
        raise HomeAssistantError(f"`{url}` is not an image")

    image["url"] = f"data:{mime_type};base64,{encode_image(url)}"
    return image


def encode_image(image_path):
    """Convert to base64 encoded image."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
