
from controllers.petcreator.main import PetCreatorController
from controllers.pets.main import PetsController
from models.main import Model
from views.main import View

class Controller:
	def __init__(self, model: Model, view: View) -> None:
		self.view = view
		self.model = model

		# initiate controllers here
		self.pets_controller = PetsController(self.model, self.view)
		self.pet_creator_controller = PetCreatorController(self.model, self.view)

	def start(self):
		self.view.start_mainloop()