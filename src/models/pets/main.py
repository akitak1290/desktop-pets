import json
import ntpath
import os
import logging
import tempfile

from models.base import ObservableModel
from models.pets.pet import PetData
from utils import ROOT_DIR

class PetsManager(ObservableModel):
	def __init__(self):
		super().__init__()
		self.logger = logging.getLogger(__name__)

		self.pets_data = {}
		self.load_pets_data()
    
	def load_pets_data(self):
		# load available pets
		pet_data_path = os.path.join(ROOT_DIR, "petdata.json")
		pets_configs_list = None
		with open(pet_data_path) as config_json:
			try:
				pets_configs_list = json.load(config_json)
			except json.JSONDecodeError:
				pets_configs_list = []
				logging.error("Failed to read config json file")

		for config_dict in pets_configs_list:
			abs_path = config_dict["abs_path"]
			data = PetData(sequence=config_dict["sequence"],
						   weights=config_dict["weights"],
						   movement_speeds=config_dict["movement_speeds"],
						   playback_speeds=config_dict["playback_speeds"],
						   storage_path=config_dict["abs_path"])

			self.pets_data[ntpath.basename(abs_path)] = data