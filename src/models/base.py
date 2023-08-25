# The base for all model object
# An observable object that allows callers to add event listeners
# and trigger those events accordingly.
class ObservableModel:
	def __init__(self):
		self._event_listeners = {}

	def add_event_listener(self, event, fn):
		try:
			self._event_listeners[event].append(fn)
		except KeyError:
			self._event_listeners[event] = [fn]
			
		return lambda: self._event_listeners[event].remove(fn)

	def trigger_event(self, event):
		if event not in self._event_listeners.keys():
			return

		for func in self._event_listeners[event]:
			func(self)