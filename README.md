## Original Project: [openai_response](https://github.com/Hassassistant/openai_response)

In addition to having updated the code for access to the new openai APIs, I added the ability to set the maximum number of tokens for each service call. 

## Installation
**1.** Copy the **openai_response** folder to your Home Assistant's custom_components directory. If you don't have a **custom_components** directory, create one in the same directory as your **configuration.yaml** file.

**2.** Add the following lines to your Home Assistant **configuration.yaml** file or create **openai.yaml** into /packages if you have already configured it, and put:
```yaml
sensor:
  - platform: openai_response
    api_key: YOUR_OPENAI_API_KEY
    model: "gpt-3.5-turbo" # Optional, defaults to "gpt-3.5-turbo"
    name: "hassio_openai_response" # Optional, defaults to "hassio_openai_response" # Optional
    instructions: "Act like a virtual assistant and provide clear information" # Optional
    max_tokens: 350 # Optional
```
Replace **YOUR_OPENAI_API_KEY** with your actual OpenAI API key.

**3.** Restart Home Assistant.

## Usage
Create an **input_text.gpt_input** entity in Home Assistant to serve as the input for the GPT-3 model. Add the following lines to your configuration.yaml file:

```yaml
input_text:
  gpt_input:
    name: GPT-3 Input
```
Note you can also create this input_text via the device helpers page!

If you are creating via YAML, you will need to restart again to activate the new entity,

To generate a response from GPT-3, update the **input_text.gpt_input** entity with the text you want to send to the model. The generated response will be available as an attribute of the **sensor.hassio_openai_response** entity.

## Example
To display the GPT-3 input and response in your Home Assistant frontend, add the following to your **ui-lovelace.yaml** file or create a card in the Lovelace UI:

```yaml
type: grid
square: false
columns: 1
cards:
  - type: entities
    entities:
      - entity: input_text.gpt_input
  - type: markdown
    content: '{{ state_attr(''sensor.hassio_openai_response'', ''response_text'') }}'
    title: ChatGPT Response
```
Now you can type your text in the GPT-3 Input field, and the generated response will be displayed in the response card.

## License
This project is licensed under the MIT License - see the **[LICENSE](https://chat.openai.com/LICENSE)** file for details.

**Disclaimer:** This project is not affiliated with or endorsed by OpenAI. Use the GPT-3 /4 API at your own risk, and be aware of the API usage costs associated with the OpenAI API.
