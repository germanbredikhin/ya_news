from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News

User = get_user_model()


class TestCommentCreation(TestCase):
    COMMENT_TEXT = 'Comment text'

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(
            title='News title',
            text='News Text'
        )
        cls.url = reverse('news:detail', args=(cls.news.pk,))
        cls.user = User.objects.create(username='test_user')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {'text': cls.COMMENT_TEXT}

    def test_unauth_cant_create_comment(self):
        self.client.post(self.url, data=self.form_data)
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)

    def test_auth_can_create_comment(self):
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, f'{self.url}#comments')
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, self.COMMENT_TEXT)

    def test_bad_words_handling(self):
        bad_words_data = {
            'text': f'Text contains {BAD_WORDS[0]},  blah blah blah'
        }
        response = self.auth_client.post(self.url, data=bad_words_data)
        self.assertFormError(
            response,
            form='form',
            field='text',
            errors=WARNING
        )
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)


class CpmmentEditDelete(TestCase):
    COMMENT_TEXT = 'comment text'
    NEW_COMMENT_TEXT = 'new comment text'

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(
            title='News title',
            text='News Text'
        )
        news_url = reverse('news:detail', args=(cls.news.pk,))
        cls.url_to_comment = news_url + '#comments'
        cls.author = User.objects.create(username='comment_author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='comment_reader')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text=cls.COMMENT_TEXT
        )
        cls.edit_url = reverse('news:edit', args=(cls.comment.id,))
        cls.delete_url = reverse('news:delete', args=(cls.comment.id,))
        cls.form_data = {'text': cls.NEW_COMMENT_TEXT}

    def test_author_can_delete_comment(self):
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 1)
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.url_to_comment)
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)

    def test_reader_cant_delete_comment(self):
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 1)
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 1)

    def test_author_can_edit_comment(self):
        response = self.author_client.post(
            self.edit_url,
            data=self.form_data
        )
        self.assertRedirects(response, self.url_to_comment)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, self.NEW_COMMENT_TEXT)

    def test_reader_cant_edit_comment(self):
        response = self.reader_client.post(
            self.edit_url,
            data=self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(self.comment.text, self.COMMENT_TEXT)
