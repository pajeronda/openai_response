from openai import OpenAI
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_API_KEY, CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change  # Importazione diretta
import logging

_LOGGER = logging.getLogger(__name__)

ATTR_MODEL = "model"
ATTR_INSTRUCTIONS = "instructions"
ATTR_PROMPT = "prompt"
CONF_MODEL = "model"
CONF_INSTRUCTIONS = "instructions"
DEFAULT_NAME = "hassio_openai_response"
DEFAULT_MODEL = "gpt-3.5-turbo"
DEFAULT_INSTRUCTIONS = "You are a helpful assistant"
DOMAIN = "openai_response"
SERVICE_OPENAI_INPUT = "openai_input"
ATTR_TOKEN = "max_tokens"
CONF_TOKEN = "max_tokens"
DEFAULT_TOKEN = 350

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string,
        vol.Optional(CONF_INSTRUCTIONS, default=DEFAULT_INSTRUCTIONS): cv.string,
        vol.Optional(CONF_TOKEN, default=DEFAULT_TOKEN): cv.positive_int,
    }
)

async def async_setup_platform(
    hass: HomeAssistant, config, async_add_entities, discovery_info=None
):
    """Setting up the sensor"""
    api_key = config[CONF_API_KEY]
    name = config[CONF_NAME]
    model = config[CONF_MODEL]
    instructions = config[CONF_INSTRUCTIONS]
    max_tokens = config[CONF_TOKEN]

    client = OpenAI(api_key=api_key)  # Set the API key during client initialization

    sensor = OpenAIResponseSensor(hass, name, model, instructions, max_tokens, client)
    async_add_entities([sensor], True)

    @callback
    async def async_generate_openai_request(service):
        """Handling service call"""
        _LOGGER.debug(service.data)
        sensor.request_running(
            service.data.get(ATTR_MODEL, config[CONF_MODEL]),
            service.data.get(ATTR_PROMPT),
            service.data.get(ATTR_INSTRUCTIONS, config[CONF_INSTRUCTIONS]),
            service.data.get(ATTR_TOKEN, config[CONF_TOKEN]),
        )
        response = await hass.async_add_executor_job(
            generate_openai_response_sync,
            service.data.get(ATTR_MODEL, config[CONF_MODEL]),
            service.data.get(ATTR_PROMPT),
            service.data.get(ATTR_INSTRUCTIONS, config[CONF_INSTRUCTIONS]),
            service.data.get(ATTR_TOKEN, config[CONF_TOKEN]),
            client,  # Pass the client object as a parameter
        )
        _LOGGER.debug(response)
        sensor.response_received(response.choices[0].message.content)  # Corrected response handling

    hass.services.async_register(
        DOMAIN, SERVICE_OPENAI_INPUT, async_generate_openai_request
    )
    return True

def generate_openai_response_sync(model: str, prompt: str, instructions: str, max_tokens: int, client: OpenAI):
    """Do the real OpenAI request"""
    _LOGGER.debug("Model: %s, Instructions: %s, Prompt: %s", model, instructions, prompt)
    return client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt},
        ]
    )

class OpenAIResponseSensor(SensorEntity):
    """The OpenAI sensor"""

    def __init__(self, hass: HomeAssistant, name: str, model: str, instructions: str, max_tokens: int, client: OpenAI) -> None:
        self._hass = hass
        self._name = name
        self._model = model
        self._DEFAULT_INSTRUCTIONS = instructions
        self._instructions = None
        self._prompt = None
        self._max_tokens = max_tokens
        self._client = client  # Add the client as an attribute
        self._attr_native_value = None
        self._response_text = ""

    @property
    def name(self):
        return self._name

    @property
    def extra_state_attributes(self):
        return {
            "response_text": self._response_text,
            "instructions": self._instructions,
            "prompt": self._prompt,
            "model": self._model,
            "max_tokens": self._max_tokens
        }

    def request_running(self, model, prompt, instructions=None, max_tokens=None):
        """Starting a new request"""
        self._model = model
        self._prompt = prompt
        self._max_tokens = max_tokens or self._max_tokens
        self._instructions = instructions or self._DEFAULT_INSTRUCTIONS
        self._response_text = ""
        self._attr_native_value = "requesting"
        self.async_write_ha_state()

    def response_received(self, response_text):
        """Updating the sensor state"""
        self._response_text = response_text
        self._attr_native_value = "response_received"
        self.async_write_ha_state()

    async def async_generate_openai_response(self, entity_id, old_state, new_state):
        """Updating the sensor from the input_text"""
        new_text = new_state.state

        if new_text:
            self.request_running(self._model, new_text)
            response = await self._hass.async_add_executor_job(
                generate_openai_response_sync,
                self._model,
                new_text,
                self._instructions,
                self._max_tokens,
                self._client,
            )
            self.response_received(response.choices[0].message.content)

    async def async_added_to_hass(self):
        """Added to hass"""
        self.async_on_remove(
            async_track_state_change(
                self._hass, "input_text.gpt_input", self.async_generate_openai_response
            )
        )

    async def async_update(self):
        """Ignore other updates"""
        pass
