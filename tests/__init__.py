from cryptojwt.utils import importer
from fedservice.entity import FederationEntity
from fedservice.entity.utils import get_federation_entity

CRYPT_CONFIG = {
    "kwargs": {
        "keys": {
            "key_defs": [
                {"type": "OCT", "use": ["enc"], "kid": "password"},
                {"type": "OCT", "use": ["enc"], "kid": "salt"},
            ]
        },
        "iterations": 1,
    }
}

SESSION_PARAMS = {"encrypter": CRYPT_CONFIG}

RESPONSE_TYPES_SUPPORTED = [
    ["code"],
    ["token"],
    ["id_token"],
    ["code", "token"],
    ["code", "id_token"],
    ["id_token", "token"],
    ["code", "token", "id_token"],
    ["none"],
]


def create_trust_chain_messages(leaf, *entity):
    where_and_what = {}

    if isinstance(leaf, str):
        pass
    else:
        _endpoint = get_federation_entity(leaf).server.get_endpoint('entity_configuration')
        where_and_what[_endpoint.full_path] = _endpoint.process_request({})["response"]

    for n in range(0, len(entity)):
        ent = entity[n]
        if isinstance(ent, FederationEntity):
            _entity = ent
        else:  # A Combo
            _entity = ent['federation_entity']

        _endpoint = _entity.server.get_endpoint('entity_configuration')

        where_and_what[_endpoint.full_path] = _endpoint.process_request({})["response"]

        _endpoint = _entity.server.get_endpoint('fetch')
        if n == 0:
            if isinstance(leaf, str):
                _sub = leaf
            else:
                _sub = leaf.entity_id
        else:
            _sub = entity[n - 1].entity_id
        _req = _endpoint.parse_request({'iss': ent.entity_id, 'sub': _sub})
        where_and_what[_endpoint.full_path] = _endpoint.process_request(_req)["response_msg"]

    return where_and_what


def create_trust_chain(leaf, *entity):
    chain = []

    if isinstance(leaf, str):
        pass
    else:
        _endpoint = get_federation_entity(leaf).server.get_endpoint('entity_configuration')
        chain.append(_endpoint.process_request({})["response"])

    for n in range(0, len(entity)):
        ent = entity[n]
        if isinstance(ent, FederationEntity):
            _entity = ent
        else:  # A Combo
            _entity = ent['federation_entity']

        _endpoint = _entity.server.get_endpoint('entity_configuration')

        # chain.append(_endpoint.process_request({})["response"])

        _endpoint = _entity.server.get_endpoint('fetch')
        if n == 0:
            if isinstance(leaf, str):
                _sub = leaf
            else:
                _sub = leaf.entity_id
        else:
            _sub = entity[n - 1].entity_id
        _req = _endpoint.parse_request({'iss': ent.entity_id, 'sub': _sub})
        chain.append(_endpoint.process_request(_req)["response"])

    return chain


def execute_function(function, **kwargs):
    if isinstance(function, str):
        return importer(function)(**kwargs)
    else:
        return function(**kwargs)


def federation_setup():
    TA_ID = "https://ta.example.org"
    WP_ID = "https://wp.example.org"
    PID_ID = "https://pid.example.org"

    entity = {}

    ##################
    # TRUST ANCHOR
    ##################

    kwargs = {
        "entity_id": TA_ID,
        "preference": {
            "organization_name": "The example federation operator",
            "homepage_uri": "https://ta.example.com",
            "contacts": "operations@ta.example.com"
        }
    }
    try:
        trust_anchor = execute_function('entities.ta.main', **kwargs)
    except ModuleNotFoundError:
        trust_anchor = execute_function('tests.entities.ta.main', **kwargs)

    trust_anchors = {TA_ID: trust_anchor.keyjar.export_jwks()}
    entity["trust_anchor"] = trust_anchor

    ########################################
    # Wallet provider
    ########################################

    kwargs = {
        "entity_id": WP_ID,
        "preference": {
            "organization_name": "The Wallet Provider",
            "homepage_uri": "https://wp.example.com",
            "contacts": "operations@wp.example.com"
        },
        "authority_hints": [TA_ID],
        "trust_anchors": trust_anchors
    }
    try:
        wallet_provider = execute_function('entities.wallet_provider.main', **kwargs)
    except ModuleNotFoundError:
        wallet_provider = execute_function('tests.entities.wallet_provider.main', **kwargs)

    trust_anchor.server.subordinate[WP_ID] = {
        "jwks": wallet_provider['federation_entity'].keyjar.export_jwks(),
        'authority_hints': [TA_ID],
        "registration_info": {"entity_types": ["federation_entity", "wallet_provider"]},
    }
    entity["wallet_provider"] = wallet_provider


    #########################################
    # OpenidCredentialIssuer - PID version
    #########################################


    kwargs = {
        "entity_id": PID_ID,
        "preference": {
            "organization_name": "The OpenID PID Credential Issuer",
            "homepage_uri": "https://pid.example.com",
            "contacts": "operations@pid.example.com"
        },
        "authority_hints": [TA_ID],
        "trust_anchors": trust_anchors
    }

    try:
        pid = execute_function('entities.pid.main', **kwargs)
    except ModuleNotFoundError:
        pid = execute_function('tests.entities.pid.main', **kwargs)

    trust_anchor.server.subordinate[PID_ID] = {
        "jwks": pid['federation_entity'].keyjar.export_jwks(),
        'authority_hints': [TA_ID],
        "registration_info": {"entity_types": ["federation_entity", "openid_credential_issuer"]},
    }
    entity["pid_issuer"] = pid

    return entity


WALLET_ID = "s6BhdRkqt3"


def wallet_setup(federation):
    #########################################
    # Wallet
    #########################################

    _anchor = federation["trust_anchor"]
    trust_anchors = {_anchor.entity_id: _anchor.keyjar.export_jwks()}

    kwargs = {
        "entity_id": WALLET_ID,
        "trust_anchors": trust_anchors
    }
    try:
        wallet = execute_function('entities.wallet.main', **kwargs)
    except ModuleNotFoundError:
        wallet = execute_function('tests.entities.wallet.main', **kwargs)

    # Need the wallet providers public keys. Could get this from the metadata
    wallet["federation_entity"].keyjar.import_jwks(
        federation["wallet_provider"]["wallet_provider"].context.keyjar.export_jwks(),
        federation["wallet_provider"].entity_id)

    return wallet
