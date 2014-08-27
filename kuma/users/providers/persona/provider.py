from allauth.socialaccount import providers

from allauth.socialaccount.providers.persona.provider import PersonaProvider


class KumaPersonaProvider(PersonaProvider):
    package = 'kuma.users.providers.persona'


providers.registry.register(KumaPersonaProvider)
