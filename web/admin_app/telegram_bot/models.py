from django.db import models


class User(models.Model):
    chat_id = models.IntegerField(primary_key=True)
    first_name = models.CharField()
    last_name = models.CharField(null=True, blank=True)
    username = models.CharField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.first_name + str(self.username) + str(self.chat_id)


class FAQArticle(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField()
    text = models.TextField()

    def __str__(self):
        return self.title


class Item(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField()
    description = models.TextField()
    category = models.CharField()
    subcategory = models.CharField()
    media = models.FileField(upload_to="media")

    def __str__(self):
        return self.name


class CartItem(models.Model):
    id = models.IntegerField(primary_key=True)
    chat_id = models.ForeignKey(User, on_delete=models.CASCADE)
    item_id = models.ForeignKey(Item, on_delete=models.CASCADE)
    item_amount = models.IntegerField()

    def __str__(self):
        return str(self.chat_id)
