from apispec import APISpec
from marshmallow import fields, Schema
from apispec.ext.marshmallow import MarshmallowPlugin

from oapi_builder.models import (
    OAuthFlowObject, OAuthFlowsObject, SecuritySchemeObject, OperationObject, RequestBodyObject, ResponseObject
)

OAUTH_URL = 'https://service-name.domain.com/api/oauth'
oauth_security = SecuritySchemeObject(type='oauth2', description='Default OAuth2', flows=OAuthFlowsObject(
    implicit=OAuthFlowObject(authorization_url=f'{OAUTH_URL}/dialog', scopes={}).to_dict(),
    authorization_code=OAuthFlowObject(
        authorization_url=f'{OAUTH_URL}/dialog', token_url=f'{OAUTH_URL}/token', scopes={}
    ).to_dict()
).to_dict()).to_dict()


spec = APISpec(
    title="Service Name",
    version="0.1.0",
    openapi_version="3.0.1",
    servers=[
        {'url': 'https://service-name.s.domain.com', 'description': 'Staging (R02)'},
        {'url': 'https://service-name.domain.com', 'description': 'Production (US-East-1)'},
        {'url': 'https://service-name.euc1.domain.com', 'description': 'Production (EU-Central-1)'},
    ],
    security=[{'default_oauth': []}],
    plugins=[MarshmallowPlugin()],
)
spec.components.security_schemes = {'default_oauth': oauth_security}

SUPPORTED_MEDIA_FEEDS = ('reddit', 'instagram', 'hackernews', 'twitter')

user_feed_media_feed_metadata = dict(
        description=f'The type of media feed the object represents. <br />'
                    f'Options:<br />   - {"<br />   - ".join(SUPPORTED_MEDIA_FEEDS)}'
    )
user_feed_username_metadata = dict(description="The user's username for the media feed.")
user_feed_priority_metadata = dict(description='How high this feed should be boosted in the page.', doc_default="1")


class UserFeedGetResponse(Schema):
    media_feed = fields.Str(metadata=user_feed_media_feed_metadata)
    username = fields.Str(metadata=user_feed_username_metadata)
    priority = fields.Int(default=1, metadata=user_feed_priority_metadata)


class UserFeedPostRequest(Schema):
    media_feed = fields.Str(required=True, metadata=user_feed_media_feed_metadata)
    username = fields.Str(required=True, metadata=user_feed_username_metadata)
    priority = fields.Int(default=1, metadata=user_feed_priority_metadata)


class UserFeedPutRequest(Schema):
    username = fields.Str(metadata=user_feed_username_metadata)
    priority = fields.Int(metadata=user_feed_priority_metadata)


class UserFeedDetailParam(Schema):
    media_feed = fields.Str(metadata=user_feed_media_feed_metadata)


STANDARD_GET_RESPONSES = ResponseObject.get_defaults([400, 401, 403, 404, 418, 429])
STANDARD_POST_RESPONSES = ResponseObject.get_defaults([204, 400, 401, 418, 429])

FEED_TAGS = ['Feed']

"""
GET /feed/{media_feed}
"""
feed_get_example = UserFeedGetResponse().dump(dict(media_feed='reddit', username='test_user'))
feed_get_200 = ResponseObject(status_code=200)
feed_get_200.set_content(UserFeedGetResponse, feed_get_example)

feed_get_operation = OperationObject(description='Retrieve details for a single feed of a user', tags=FEED_TAGS)
feed_get_operation.add_parameter(UserFeedDetailParam, 'media_feed')
feed_get_operation.upsert_responses(STANDARD_GET_RESPONSES + [feed_get_200])

"""
PUT /feed/{media_feed}
"""
feed_put_example = UserFeedPutRequest().dump(dict(priority=5))
feed_put_request = RequestBodyObject(description='Request body to create a feed for a user', required=True)
feed_put_request.set_content(UserFeedPostRequest, feed_put_example)

feed_put_response_example = UserFeedGetResponse().dump(dict(media_feed='reddit', username='test_user', priority=5))
feed_put_200 = ResponseObject(status_code=200)
feed_put_200.set_content(UserFeedGetResponse, feed_put_response_example)

feed_put_operation = OperationObject(description='Create a feed for a user', tags=FEED_TAGS)
feed_put_operation.add_parameter(UserFeedDetailParam, 'media_feed')
feed_put_operation.request_body = feed_put_request
feed_put_operation.upsert_responses(STANDARD_GET_RESPONSES + [feed_put_200])

"""
DELETE /feed/{media_feed}
"""
feed_del_operation = OperationObject(description='Remove a user feed', tags=FEED_TAGS)
feed_del_operation.add_parameter(UserFeedDetailParam, 'media_feed')
feed_del_operation.upsert_responses(STANDARD_POST_RESPONSES)

"""
LIST /feed
"""
feed_list_200 = ResponseObject(status_code=200)
feed_list_200.set_content(UserFeedGetResponse, [
    UserFeedGetResponse().dump(dict(media_feed=media_feed, username=f'test_user.{media_feed}'))
    for media_feed in SUPPORTED_MEDIA_FEEDS
])

feed_list_operation = OperationObject(description='Retrieve a list of feeds for a user', tags=FEED_TAGS)
feed_list_operation.upsert_responses(STANDARD_GET_RESPONSES)
feed_list_operation.upsert_responses([feed_list_200])

"""
POST /feed
"""
feed_post_example = UserFeedPostRequest().dump(dict(media_feed='reddit', username='test_user'))
feed_post_request = RequestBodyObject(description='Request body to create a feed for a user', required=True)
feed_post_request.set_content(UserFeedPostRequest, feed_post_example)

feed_post_operation = OperationObject(description='Create a feed for a user', tags=FEED_TAGS)
feed_post_operation.request_body = feed_post_request
feed_post_operation.upsert_responses(STANDARD_POST_RESPONSES)

spec.path(
    path="/feed",
    operations=dict(get=feed_list_operation.to_dict(), post=feed_post_operation.to_dict())
).path(
    path="/feed/{media_feed}",
    operations=dict(get=feed_get_operation.to_dict(), delete=feed_del_operation.to_dict())
)

with open('swagger.yaml', 'w') as f:
    f.write(spec.to_yaml())

