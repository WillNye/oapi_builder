from apispec import APISpec
from marshmallow import fields, Schema
from apispec.ext.marshmallow import MarshmallowPlugin

from oapi_builder.models import ResponseObject, OperationObject


spec = APISpec(
    title="Service Name",
    version="0.1.0",
    openapi_version="3.0.1",
    servers=[
        {'url': 'http://service-name.s.domain.com', 'description': 'Staging (R02)'},
        {'url': 'http://service-name.domain.com', 'description': 'Production (US-East-1)'},
        {'url': 'http://service-name.euc1.domain.com', 'description': 'Production (EU-Central-1)'},
    ],
    plugins=[MarshmallowPlugin()],
)

SUPPORTED_MEDIA_FEEDS = ('reddit', 'instagram', 'hackernews', 'twitter')


class UserFeedGet(Schema):
    media_feed = fields.Str(metadata=dict(
        description=f'The type of media feed the object represents. <br />'
                    f'Options:<br />   - {"<br />   - ".join(SUPPORTED_MEDIA_FEEDS)}'
    ))
    username = fields.Str(metadata=dict(
        description="The user's username for the media feed."
    ))
    priority = fields.Int(
        default=1,
        metadata=dict(description='How high this feed should be boosted in the page.', doc_default="1")
    )


standard_responses = ResponseObject.get_defaults([400, 401, 403, 404, 418, 429])

feed_get_example = UserFeedGet().dump(dict(media_feed='reddit', username='test_user'))
feed_get_200 = ResponseObject(status_code=200)
feed_get_200.set_content(UserFeedGet, feed_get_example)

feed_get_operation = OperationObject(description='Retrieve a list of feeds for a user')
feed_get_operation.upsert_responses(standard_responses)
feed_get_operation.upsert_responses([feed_get_200])

spec.path(
    path="/feed",
    operations=dict(get=feed_get_operation.to_dict())
)

with open('swagger.yaml', 'w') as f:
    f.write(spec.to_yaml())

