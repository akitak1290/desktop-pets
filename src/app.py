import logging
import os

from models.main import Model
from views.main import View
from controllers.main import Controller

ROOT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
LOG_FILE_PATH = os.path.join(ROOT_DIR_PATH, 'runtime.log')



def main():
	logging.basicConfig(filename=LOG_FILE_PATH, filemode='w',
					format='%(name)s - %(levelname)s - %(message)s',
					level=logging.DEBUG)

	model = Model()
	view = View()
	controller = Controller(model, view)
	controller.start()

if __name__ == "__main__":
    main()