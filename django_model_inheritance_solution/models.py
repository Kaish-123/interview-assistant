"""Models for the PersonBase / WorkerBase / Student / Teacher challenge."""

from django.db import models


class PersonBase(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255, blank=False)
    last_name = models.CharField(max_length=255, blank=False)

    class Meta:
        abstract = True
        ordering = ("last_name", "first_name", "id")

    def __new__(cls, *args, **kwargs):
        if cls is PersonBase:
            inst = _PersonBaseConcrete(*args, **kwargs)
            inst._skip_personbase_outer_init = True
            return inst
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        if getattr(self, "_skip_personbase_outer_init", False):
            del self._skip_personbase_outer_init
            return
        super().__init__(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class _PersonBaseConcrete(PersonBase):
    class Meta:
        abstract = False


class WorkerBase(PersonBase):
    experience = models.IntegerField(default=0)

    class Meta:
        abstract = True


class Student(PersonBase):
    faculty = models.CharField(max_length=255, blank=False)


class Teacher(WorkerBase):
    title = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-experience",)

    @property
    def full_name(self):
        parts = []
        if self.title:
            parts.append(self.title)
        parts.extend([self.first_name, self.last_name])
        return " ".join(parts)
