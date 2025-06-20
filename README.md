# Better Conversation

This is a custom component for Home Assistant that enhances the conversation experience with persistent memory and advanced features.

Derived from [Extended OpenAI Conversation](https://github.com/jekalmin/extended_openai_conversation) with significant improvements.

## Key Features

### 🧠 **Persistent Memory** (NEW!)

- **Conversation History Persistence**: Your conversations are now saved and persist across Home Assistant restarts
- **Automatic Cleanup**: Old conversations are automatically cleaned up to prevent storage bloat
- **Configurable Memory**: Set how many conversations to keep in memory (default: 50)
- **Manual History Management**: Clear conversation history via service call

### 🔧 **Enhanced Functionality**

- Ability to call services of Home Assistant
- Ability to create automations
- Ability to get data from external APIs or web pages
- Ability to retrieve state history of entities
- Option to pass the current user's name to OpenAI via the user message context

## How it works

Better Conversation uses OpenAI API's feature of [function calling](https://platform.openai.com/docs/guides/function-calling) to call services of Home Assistant.

Since OpenAI models already know how to call services of Home Assistant in general, you just have to let the model know what devices you have by [exposing entities](https://github.com/jekalmin/extended_openai_conversation#preparation).

## Installation

1. Install via registering as a custom repository of HACS or by copying `better_conversation` folder into `<config directory>/custom_components`
2. Restart Home Assistant
3. Go to Settings > Devices & Services.
4. In the bottom right corner, select the Add Integration button.
5. Follow the instructions on screen to complete the setup (API Key is required).
   - [Generating an API Key](https://www.home-assistant.io/integrations/openai_conversation/#generate-an-api-key)
   - Specify "Base Url" if using OpenAI compatible servers like Azure OpenAI (also with APIM), LocalAI, otherwise leave as it is.
6. Go to Settings > [Voice Assistants](https://my.home-assistant.io/redirect/voice_assistants/).
7. Click to edit Assistant (named "Home Assistant" by default).
8. Select "Better Conversation" from "Conversation agent" tab.

## Configuration

### Memory Settings

In the integration options, you can configure:

- **Maximum conversations to store in memory**: Controls how many conversations are kept in persistent storage (default: 50)
- **Context threshold**: Maximum tokens before truncation (default: 13000)
- **Context truncation strategy**: How to handle long conversations (default: Clear All Messages)

### Services

#### `better_conversation.clear_history`

Clear all conversation history for a specific integration instance.

**Service Data:**

```yaml
config_entry: "your_config_entry_id"
```

**Example:**

```yaml
service: better_conversation.clear_history
data:
  config_entry: "your_config_entry_id"
```

#### `better_conversation.get_history`

Get conversation history for debugging purposes.

**Service Data:**

```yaml
config_entry: "your_config_entry_id"
```

**Example:**

```yaml
service: better_conversation.get_history
data:
  config_entry: "your_config_entry_id"
```

**Response:**

```yaml
{
  "history":
    {
      "device_id_user_id":
        {
          "message_count": 5,
          "last_message": "The assistant's last response",
          "conversation_id": "01H...",
        },
    },
}
```

#### `better_conversation.refresh_prompts`

Force refresh all system messages in existing conversations. Use this when you change the prompt template and want existing conversations to use the new prompt immediately.

**Service Data:**

```yaml
config_entry: "your_config_entry_id"
```

**Example:**

```yaml
service: better_conversation.refresh_prompts
data:
  config_entry: "your_config_entry_id"
```

**Response:**

```yaml
{ "refreshed_count": 3 }
```

## Preparation

After installation, you need to expose entities from "http://{your-home-assistant}/config/voice-assistants/expose".

## What's New in Better Conversation

### Memory Management

- **Persistent Storage**: Conversations are now saved to Home Assistant's storage system
- **Automatic Loading**: History is automatically loaded when the component starts
- **Smart Cleanup**: Old conversations are automatically removed to prevent storage issues
- **Manual Control**: Clear history via service call when needed
- **Fixed Conversation Tracking**: Proper conversation context maintenance within sessions
- **Dynamic Prompt Updates**: System messages automatically refresh when prompt template changes

### Configuration Options

- **Max Conversations**: Configure how many conversations to keep in memory
- **Enhanced UI**: Better configuration interface with new memory options

### Debugging Tools

- **Get History Service**: Retrieve conversation history for debugging
- **Debug Logging**: Enhanced logging to track conversation keys and IDs

### Prompt Template Issues

- **Prompt not updating**: If you change the prompt template but existing conversations don't use it:
  1. Use the `better_conversation.refresh_prompts` service to force update all conversations
  2. Or clear conversation history with `better_conversation.clear_history`
  3. Enable debug logging to see which prompt template is being used
- **Template errors**: Check the logs for template rendering errors
- **Prompt debugging**: The system logs which prompt template is being used (first 100 characters)

### Performance

- Large conversation histories may impact performance
- Consider reducing the max conversations setting if you experience slowdowns
- The component automatically cleans up old conversations to maintain performance

## Examples

### 1. Turn on single entity

User: "Turn on the living room light"

Assistant: "I'll turn on the living room light for you."

### 2. Create automation

User: "Create an automation to turn on the porch light at sunset"

Assistant: "I'll create an automation to turn on the porch light at sunset."

### 3. Get history with memory

User: "What did we talk about earlier?"

Assistant: "Earlier we discussed turning on the living room light and creating an automation for the porch light at sunset."

## Migration from Extended OpenAI Conversation

If you're upgrading from Extended OpenAI Conversation:

1. **Backup your configuration**: Export your current configuration
2. **Install Better Conversation**: Follow the installation steps above
3. **Configure the new integration**: Set up with your existing API key
4. **Update your voice assistant**: Change the conversation agent to "Better Conversation"
5. **Enjoy persistent memory**: Your conversations will now persist across restarts!

## Troubleshooting

### Memory Issues

- If you experience storage issues, reduce the "Maximum conversations" setting
- Use the `better_conversation.clear_history` service to clear all history
- Check the logs for any storage-related errors

### Conversation Tracking Issues

- **Context not preserved**: If conversations still don't remember context, enable debug logging:
  ```yaml
  logger:
    logs:
      custom_components.better_conversation: debug
  ```
- **Check conversation keys**: Use the `better_conversation.get_history` service to see if conversations are being tracked properly
- **Device/User identification**: Ensure your device_id and user_id are being properly passed to the conversation system

### Prompt Template Issues

- **Prompt not updating**: If you change the prompt template but existing conversations don't use it:
  1. Use the `better_conversation.refresh_prompts` service to force update all conversations
  2. Or clear conversation history with `better_conversation.clear_history`
  3. Enable debug logging to see which prompt template is being used
- **Template errors**: Check the logs for template rendering errors
- **Prompt debugging**: The system logs which prompt template is being used (first 100 characters)

### Performance

- Large conversation histories may impact performance
- Consider reducing the max conversations setting if you experience slowdowns
- The component automatically cleans up old conversations to maintain performance

## Contributing

This component is based on the excellent work of the Extended OpenAI Conversation project. Contributions are welcome!

## License

This project is licensed under the same terms as the original Extended OpenAI Conversation project.
