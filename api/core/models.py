from django.db import models

# Create your models here.


class Opening(models.Model):
	is_white = models.BooleanField()
	slug     = models.CharField(max_length=255)

	def __str__(self):
		return str('white' if self.is_white else 'black') + ' - ' + str(self.slug)


class Move(models.Model):
	start = models.CharField(max_length=16) # Start square
	end   = models.CharField(max_length=16) # End square
	line  = models.TextField() # e2e4 e7e5 ...
	score = models.DecimalField(max_digits=10, decimal_places=2)
	type  = models.CharField(max_length=100) # best, candidate

	def __str__(self):
		return str(self.line)


class Line(models.Model):
	line  = models.TextField() # e2e4 e7e5 ...
	san   = models.TextField() # e4 e5 ... Standard algebraic notation
	slug  = models.CharField(max_length=255)

	def __str__(self):
		return str(self.slug) + ' - ' + str(self.san)
