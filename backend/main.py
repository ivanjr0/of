from datetime import datetime

from django.db import models
from nanodjango import Django

from redis import Redis
from rq import Queue

app = Django()


@app.admin
class Content(models.Model):
    name = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed = models.BooleanField(default=False)


class ContentRequest(app.ninja.Schema):
    name: str
    content: str


class ContentResponse(app.ninja.Schema):
    id: int
    name: str
    content: str
    created_at: datetime
    updated_at: datetime
    processed: bool

queue = Queue(connection=Redis())

@app.api.post("/content")
def post_content(request, data: ContentRequest):
    content = Content.objects.create(
        name=data.name,
        content=data.content
    )
    queue.enqueue(process_content, content.id)
    return ContentResponse.from_orm(content)


@app.api.get("/content/{content_id}", response=ContentResponse)
def get_content(request, content_id: int):
    try:
        content = Content.objects.get(id=content_id)
    except Content.DoesNotExist:
        raise app.ninja.HTTPException(status_code=404, detail="Content not found")
    return ContentResponse.from_orm(content)


def process_content(content_id):
    content = Content.objects.get(id=content_id)
    content.processed = True
    content.save()