#!/usr/bin/env python
# -*- coding: utf-8 -*-

import types

def synchronizeEvent(event, *params):
	event.executeEvent(*params)

class Event:
	def __init__(self):
		self.handlers = []

	def __iadd__(self, handler):
		if not callable(handler):
			raise ValueError, "Event handler " + handler + " is not a FunctionType"
		self.handlers.append(handler)
		return self

	def __isub__(self, handler):
		if handler in self.handlers:
			self.handlers.remove(handler)
		return self

	def raiseEvent(self, *params):
		if len(self.handlers) != 0:
			assert callable(synchronizeEvent), "Event synchronization function not defined!"
			synchronizeEvent(self, *params)

	def executeEvent(self, *params):
		for handler in self.handlers:
			handler(*params)
