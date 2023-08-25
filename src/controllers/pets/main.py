import ntpath
import tempfile
from controllers.pets.pet import PetController

class PetsController:
	def __init__(self, model, view) -> None:
		self.model = model
		self.view = view
		self.pet_controllers = {}

		# TODO: bind element used to create pet here
		self.create_pet("tmpydlakwwy")
		# assets/pets/tmp79sasr9w

	def create_pet(self, type):
		pet_data = self.model.pets_manager.pets_data[type]

		self.pet_controllers[self._random_pet_name()] = PetController(self.model, self.view, pet_data)
	
	def remove_pet(self, name):
		self.pet_controllers[name].remove_pet() # cleanup
		self.pet_controllers.pop(name)

	def _random_pet_name(self) -> str:
		# lazy random string gen,
		# TODO: add real names
		return ntpath.basename(tempfile.NamedTemporaryFile().name)

		
