from django.db import models

# Create your models here.


class Move(models.Model):
	start = models.CharField(max_length=16) # Start square
	end   = models.CharField(max_length=16) # End square
	line  = models.TextField() # e2e4 e7e5 ...
	score = models.DecimalField(max_digits=10, decimal_places=2)
	type  = models.CharField(max_length=100) # best, candidate


	def __str__(self):
		return str(self.line)
