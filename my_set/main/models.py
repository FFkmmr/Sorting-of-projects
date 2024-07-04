from django.db import models
from django.contrib.auth.models import User


class Technology(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
    @property
    def num_projects(self):
        return self.project_set.count()


class Industry(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
    @property
    def num_projects(self):
        return self.project_set.count()


class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    url = models.CharField(max_length=100)
    technologies = models.ManyToManyField(Technology)
    description = models.TextField()
    industries = models.ManyToManyField(Industry)
    is_private = models.BooleanField(default=False)
    sets = models.ManyToManyField('MySets', blank=True, related_name='projects')

    def __str__(self):
        return self.title
    

class MySets(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    is_private = models.BooleanField(default=False)
    allowed_for = models.ManyToManyField(User, related_name='allowed_sets', blank=True)

    def __str__(self):
        return self.name