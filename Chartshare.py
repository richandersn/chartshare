#-----------------------------------------------------------------------------
# Name:        Chartshare.py
# Purpose:     A Computer based standard celeration charting system.
#
# Author:      Richard L. Anderson <anderson@unt.edu>
#
# Created:     2003/24/10
# RCS-ID:      $Id: Chartshare.py $
# Copyright:   (c) 2002, 2003
# Licence:     See LICENSE.
#-----------------------------------------------------------------------------

"""
Chartshare: A computer based system for standard celeration charting.

Chartshare is a open source, cross platform computer based system for
Standard Celeration Charting (see http://www.celeration.org for more
information on the Standard Celeration Chart) for more details.
Chartshare is an XML DTD for textually encoding standard celeration
charts and related metadata, a set of python classes for analyzing and
rendering chartshare XML documents, and an web services api for
rendering chartshare XML documents.


"""

import sys, re, StringIO

from rpy import *
from xml.sax.handler import ContentHandler
from xml.sax.saxutils import XMLGenerator
from xml.sax import make_parser

class Util:
	"""	Utility function mixin class for Chart and Chart subclasses."""
	
	def empty_array(self, values):
		"""Returns an empty list of the same size as values."""
		retval = []
		for i in values:
			retval.append('')
		return retval

	def reverse(self, value):
		"""Reverse a string."""
		strlist=list(value)
		strlist.reverse()
		return ''.join(strlist)

	def commify(self, value):
		"""Formats a number string according to chart conventions."""
		if (value < 1):
			value = "%g" % value
		value=str(value)
		r1 = re.compile(r'^0(\.\d+)')
		r2 = re.compile(r'(\d\d\d)(?=\d)(?!\d*\.)')
		if (value == '1000'):
			return value
		elif (r1.match(value)):
			return r1.match(value).group(1)
		else:
			return self.reverse(r2.sub(r'\1,',self.reverse(value)))
		
class Element(object):
	"""Base class for Chartshare vector elements."""
	def __init__(self, offset=0, value=0):
		self.offset=offset
		self.value=value
		self.text=''
	
	def setText(self, value):
		self.value=value
		
	def getText(self):
		return self.value
		
	text = property(getText, setText)

class Vector(object):
	"""Base class for Chartshare Vectors."""
	def __init__(self, name='', color='black', linetype='o', symbol=1, 
				 clutter=0, start=0, end=140, continuous=False, debug=False):
		self.name=name
		self.color=color
		self.linetype=linetype
		self.symbol=symbol
		self.start=start
		self.end=end
		self.elements={}
		self.debug=debug
		self.continuous=continuous
		
		if not self.continuous:				
			for i in range(self.start, self.end+1):
				self.elements[i]='NaN'
			
	def getSymbol(self):
		return self._symbol
	
	def setSymbol(self, value):
		if (type(value) == int):
			if (value >= 0) and (value <= 18):
				self._symbol = value
			else:
				raise SymbolOutOfRange, "Symbol should be an integer between 0 and 18."
		elif (type(value) == str):
			try:
				self._symbol = value[0]
			except IndexError:
				self._symbol=1
		else:
			self._symbol = 1	
	
	symbol = property(getSymbol, setSymbol)
	
	
	def getLinetype(self):
		return self._linetype
		
	def setLinetype(self, value):
		if (value == 'p') or (value == 'o') or (value == 'l'):
			self._linetype = value
		else:
			raise InvalidLinetype, "Line type should be 'o', 'p', or 'l'"
			
	linetype = property(getLinetype, setLinetype)
	
	def get_elements(self):
		"""Returns a list with the elements of a Vector."""
		retval = []
		for i in range(self.start, self.end+1):
			if (not self.continuous):
				retval.append(self.elements[i])
			else:
				if (self.elements[i] != 'NaN'):
					retval.append(self.elements[i])
		return retval
		
	def get_offsets(self):
		"""Returns a list of the offsets of a Vector."""
		retval = [] 
		for i in range(self.start, self.end+1):
			if (not self.continuous):
				retval.append(i)
			else:
				if (self.elements[i] == 'NaN'):
					retval.append(i)
		return retval

	def to_xml(self, container=False):
		"""Returns an xml representation of the Vector."""
		if (container == False):
			container = StringIO.StringIO()
		xml = XMLGenerator(container)
		attrs = {}
		attrs[u'name'] = u"%s" % self.name
		attrs[u'symbol'] = u"%s" % self.symbol
		attrs[u'linetype'] = u"%s" % self.linetype
		attrs[u'color'] = u"%s" % self.color
		xml.startElement(u'vector', attrs)
		for i in range(self.start, self.end+1):
			if (self.elements[i] != 'NaN'):
				attrs.clear()
				attrs[u'offset'] = u"%s" % i
				xml.startElement(u'element', attrs)
				xml.characters(u"%s" % self.elements[i])
				xml.endElement(u'element')
		xml.endElement(u'vector')
			
	def render(self):
		"""Plots the current vector."""
		if (self.debug):
			print "Rendering Vector: %s" % self.name
			print self.elements
			
		r.points(x=range(self.start, self.end+1),
				 y=self.elements,
				 col=self.color,
				 type=self.linetype,
				 pch=self.symbol)
		if (self.debug):
			print "Finished rendering Vector: %s" % self.name

class Phase(object):
	"""Base class for a phase change line."""
	def __init__(self, name='', color='black',length=.8, width=2, pos='', y_start=.001,
		y_end=1000, x_start=0, x_end=140, absolute_length='', tail_length=1, label='', debug=False):
		self.name=name
		self.color=color
		self.length=length
		self.width=width
		self.pos=pos
		self.y_start=y_start
		self.y_end=y_end
		self.x_start=x_start
		self.x_end=x_end
		self.absolute_length=absolute_length
		self.tail_length=tail_length
		self.label=label
		self.debug=debug
		
	def setText(self, value):
		self.label=value
		
	def getText(self):
		return self.label
		
	text = property(getText, setText)

		
	def _compute_y(self):
		"""Computes the length of the phase change line."""
		if (self.absolute_length):
			return self.absolute_length
		else:
			return self.y_end * self.length
			
	def to_xml(self, container=False):
		"""Prints an XML representation of the Phase object."""
		if (container == False):
			container = StringIO.StringIO()
		xml = XMLGenerator(container)
		attrs = {}
		attrs[u'name'] = u"%s" % self.name
		attrs[u'color'] = u"%s" % self.color
		attrs[u'pos'] = u"%s" % self.pos
		attrs[u'tail_length'] = u"%s" % self.tail_length
		if self.absolute_length:
			attrs[u'absolute_length'] = u"%s" % self.absolute_length
		else:
			attrs[u'length'] = u"%s" % self.length

		xml.startElement(u'phase', attrs)
		xml.characters(self.label)
		xml.endElement(u'phase')

			
	def render(self):
		"""Renders the phase change line."""

		x = [self.pos, self.pos]
		y = [self.y_start, self._compute_y()]
		
		r.lines(x=x, y=y, col=self.color, lwd=self.width)
		
		x=[self.pos, (self.pos+self.tail_length)]
		y=[self._compute_y(), self._compute_y()]
		
		r.lines(x=x, y=y, col=self.color, lwd=self.width)

		if (self.tail_length < 0):
			pos=2
		elif (self.tail_length == 0):
			pos=3
		else:
			pos=4
			
		r.text(x=(self.pos + self.tail_length), y=self._compute_y(), col=self.color, pos=pos,
			labels=self.label, cex=.75)

class Chart(object, Util):
	"""Base class for celeration charts."""
	def __init__(self, name='', x_start=0, x_end=140, period=7, cycles=6,
				 cycle_start=-3, cycle_end=3, fg='light blue', bg='white',
				 clutter=4, format='pdf', outfile='figure', chart_type='daily',
				 title='Daily Per Minute', debug=False):
				 
		self.x_start=x_start
		self.x_end=x_end
		self.period=period
		self.cycles=period
		self.cycle_start=cycle_start
		self.cycle_end=cycle_end
		self.fg=fg
		self.bg=bg
		self.clutter=clutter
		self.format=format
		self.outfile=outfile
		self.chart_type=chart_type
		self.title=title
		self.debug=debug
		self.name=name
		self.objects={}
		self._build_y()
		self._build_x()		
		
	def to_xml(self, container=False):
		"""Prints an XML representation of the Chart object."""
		
		if (container == False):
			container = StringIO.StringIO()
		xml = XMLGenerator(container)
		xml.startDocument()
		### Make sure all possible attributes are accounted for here. (rla)
		attrs = {}
		attrs[u'name']= u"%s" % self.name
		attrs[u'title'] = u"%s" % self.title
		attrs[u'type'] = u"%s" % self.chart_type
		xml.startElement(u'chart', attrs)
		### Loop through each of the objects and call it's to_xml method. (rla)
		for i in self.objects.keys():
			self.objects[i].to_xml(container=container)
		xml.endElement(u'chart')
		container.seek(0)
		return container
		
	def _start_R(self):
		"""Imports the rpy module and starts a session."""
		
	def _open_device(self):
		"""Creates and opens the plotting devices."""
		if (self.format == 'eps'):
			r.postscript(file=self.outfile, onefile=0, height=8.5, width=11)
		elif (self.format == 'png'):
			r.png(file=self.outfile, width=1024, height=768)
		elif (self.format == 'jpg'):
			r.jpeg(file=self.outfile, width=1024, height=768, quality=75)
		else:
			r.pdf(file=self.outfile, height=8.5, width=11)
			
		r.par(pin=[8, 5.25], xaxs='i', yaxs='i', col_axis=self.fg, bg=self.bg, fg=self.fg)
		self.device_status=True
		
	def _build_y(self):
		"""Builds the y axis for a Standard Celeration Chart."""
		self.y_start = (10**self.cycle_start)
		self.y_end = (10**self.cycle_end)
		
		self.ylim = [self.y_start, self.y_end]
		
		self.myticks=[]
		self.mnyticks=[]
		self.mylabs=[]
		self.mnylabs=[]
		self.yticks=[]
		
		for i in range(self.cycle_start, self.cycle_end+1):
			increment=(10**i)
			next_increment=(10**(i+1))
			self.myticks.append(increment)
			self.mylabs.append(self.commify(increment))
			mnytick=((10**(i+1))/2)
			if (mnytick < (10**self.cycle_end)):
				self.mnyticks.append(mnytick)
				self.mnylabs.append(self.commify(mnytick))
				
				for j in range(1, 10):
					self.yticks.append(j*(10**i))	
		self.yticks.append(10**self.cycle_end)
					
	def _build_x(self):
		"""Builds the x axis for a Standard Celeration Chart."""
		self.xticks = range(self.x_start, self.x_end+1)
		self.periods = range(self.x_start, self.x_end+1, self.period)
		self.mxticks = range(self.x_start, self.x_end+1, self.period*2)
		self.xlim = [self.x_start, self.x_end]
		
	def _plot_frame(self):
		"""Plots the frame for a Standard Celeration Chart."""
		
		blank_x = range(self.x_start, self.x_end+1)
		blank_y=[]
		for i in blank_x:
			blank_y.append('NaN')
		r.plot(x=blank_x, y=blank_y, xlim=self.xlim, ylim=self.ylim, 
			xlab='', ylab='', log='y', axes=False)

		r.axis(side=2, at=self.myticks, las=2, labels=self.mylabs, tck=-0.02,
			pos = self.x_start, lwd = 2, col_axis=self.fg)
			
		r.axis(side=2, at=self.myticks, tck=1.02, pos=self.x_start,
			labels=self.empty_array(self.myticks), lwd=2)

		r.axis(side=2, at=self.mnyticks, las=2, labels=self.mnylabs, pos=self.x_start,
			tck=-0.015, lwd=1.5, cex_axis=0.8)

		r.axis(side=2, at=self.mnyticks, las=2, labels=self.empty_array(self.mnyticks), tck=1.015,
			lwd=1.5)
		
		r.axis(side=2, at=self.yticks, labels=self.empty_array(self.yticks), pos=self.x_start, tck=1)

		r.axis(side=1, at=self.mxticks, pos=self.y_start, lwd=2, labels=self.mxticks, tck=-0.01)		
		
		r.axis(side=1, at=self.periods, pos=self.y_start, tck=-0.01, lwd=2, labels=self.empty_array(self.periods))
		
		r.axis(side=1, at=self.periods, pos=self.y_start, tck=1, labels=self.empty_array(self.periods), lwd=2)
		
		r.axis(side=1, at=range(self.x_start, self.x_end), pos=self.y_start,
			labels=self.empty_array(range(self.x_start, self.x_end)), tck=-0.01)

		r.axis(side=1, at=range(self.x_start,self.x_end), pos=self.y_start, tck=1,
			labels=self.empty_array(range(self.x_start, self.x_end)))
			
		r.axis(side=3, at=self.periods, pos=self.y_end, lwd=2, tck=-0.01,cex_axis=0.5,
			labels=self.empty_array(self.periods)) 

		r.box(lwd=2)
			
	def _plot_objects(self):
		"""Plots all objects in the object dictionary."""

		for i in self.objects.keys():
			self.objects[i].debug = self.debug
			self.objects[i].render()
	
	def _decorate(self):
		"""
		This is a stub for the _decorate method that adds top labels, 
		left axis notations, etc.  Chart._decorate() should do something 
		useful in subclasses.
		"""

		pass

	def _annotate(self):
		"""
		This is a stub for the _annotate method that adds annotations to
		the bottom of the chart.  Chart._annotate() should do something useful
		in subclasses.
		"""

		pass

	def _close_device(self):
		"""Closes the R graphics device."""

		r.dev_off()
		self.device_status=False
		
	def render(self):
		"""Renders the Standard Celeration Chart."""

		self._start_R()
		self._open_device()
		self._plot_frame()
		self._plot_objects()
		self._decorate()
		self._close_device()

class DailyPerMinuteChart(Chart):
	"""Daily/Minute Standard Celeration Chart."""
	
	def _decorate(self):
		"""Adds decorations to the daily celeration chart."""
		
		toplabs = range(0,21,4)
		toppos = range(0,141,28)
		r.axis(side=3, at=toppos, labels=toplabs, lwd=2, tck=-0.01)
		
		r.mtext(side=3, at=1, line=0, cex=0.4, text='M')
		r.mtext(side=3, at=3, line=0, cex=0.4, text='W')
		r.mtext(side=3, at=5, line=0, cex=0.4, text='F')
		r.mtext(side=3, at=7, line=0.5, cex=0.4, text='SUN', las=2)
		r.mtext(side=3, at=42, line=2, text='SUCCESSIVE')
		r.mtext(side=3, at=70, line=2, text='CALENDAR')
		r.mtext(side=3, at=98, line=2, text='WEEKS')
		r.mtext(side=3, line=4, cex=1.2, text=self.title)
		
		r.mtext(side=2, at=10, line=3, text='COUNT PER MINUTE')
		
		r.mtext(side=1, line=2, text='SUCCESSIVE CALENDAR DAYS')
		
		r.mtext(side=4, line=1, text='COUNTING TIMES', at=40, cex=0.75)
		
		rightpos= [.001,    .002,   .005,   .01,   .02,   .05,    .1,   .2,   .5,    1,     2,     3,    4,     6]
		rightlabs=["1000'", "500'", "200'", "100'", "50'", "20'", "10'", "5'", "2'", "1'", '30"', '20"', '15"', '10"']
		
		r.axis(side=4, las=2, at=rightpos, labels=rightlabs, tck=-0.02, cex_axis=0.75)
		
		r.mtext(side=4, las=2, at=0.025, text='hrs', line=3, cex=0.75)
		r.mtext(side=4, las=2, at=1, text='min', line=3, cex=0.75)
		r.mtext(side=4, las=2, at=6, text='sec', line=3, cex=0.75)
		
		r.mtext(side=4, las=2, at=0.001, line=4, cex=0.075, text=r('expression(- 16*degree)'))
		r.mtext(side=4, las=2, at=0.002, line=4, cex=0.075, text=r('expression(- 8*degree)'))
		r.mtext(side=4, las=2, at=0.004, line=4, cex=0.075, text=r('expression(- 4*degree)'))
		r.mtext(side=4, las=2, at=0.008, line=4, cex=0.075, text=r('expression(- 2*degree)'))
		r.mtext(side=4, las=2, at=0.015, line=4, cex=0.075, text=r('expression(- 1*degree)'))
		
class YearlyChart(Chart):
	"""Yearly Standard Celeration Chart."""
	
	def __init__(self, name='', x_start=0, x_end=100, period=5, cycles=6, cycle_start=0,
		cycle_end=6, fg='light blue', bg='white', clutter=4, format='pdf', outfile='figure',
		chart_type='yearly', title='', century=1900, debug=False):
		
		self.name=name
		self.x_start=x_start
		self.x_end=x_end
		self.period=period
		self.cycles=cycles
		self.cycle_start=cycle_start
		self.cycle_end=cycle_end
		self.fg=fg
		self.bg=bg
		self.clutter=clutter
		self.format=format
		self.outfile=outfile
		self.chart_type=chart_type
		self.title=title
		self.century=century
		self.debug=debug
		self.objects={}
		
		self._build_y()
		self._build_x()

		
	def _decorate(self):
		"""Decorates the yearly Standard Celeration Chart."""
		
		toplabs=[]
		for i in range(self.century,self.century+101,10):
			toplabs.append("%i\n________\nDECADE" % i)
			toplabs.append(5)
			
		toplabs.pop()
		
		r.mtext(side=2, line=4, text='COUNT PER YEAR')
		r.mtext(side=1, line=3, text='SUCCESSIVE CALENDAR YEARS')
		r.mtext(side=3, line=5, text='CALENDAR DECADES')
		r.mtext(side=3, line=4, text='0', at=0)
		r.mtext(side=3, line=4, text='5', at=50)
		r.mtext(side=3, line=4, text='10', at=100)
		
		r.axis(side=3, at=self.periods, labels=toplabs, lwd=2, tck=-0.01, cex_axis=0.5)
		
class DailyPerDayChart(Chart):
	"""DAILY per day Celeration Chart."""
	
	def __init__(self, name='', x_start=0, x_end=140, period=7, cycles=6,
				 cycle_start=0, cycle_end=6, fg='light blue', bg='white',
				 clutter=4, format='pdf', outfile='figure', chart_type='DailyPerDay',
				 title='DAILY per day CHART', debug=False):
				 
		self.x_start=x_start
		self.x_end=x_end
		self.period=period
		self.cycles=period
		self.cycle_start=cycle_start
		self.cycle_end=cycle_end
		self.fg=fg
		self.bg=bg
		self.clutter=clutter
		self.format=format
		self.outfile=outfile
		self.chart_type=chart_type
		self.title=title
		self.debug=debug
		self.name=name
		self.objects={}
		self._build_y()
		self._build_x()

	def _decorate(self):
		"""Adds decorations to the daily celeration chart."""
		
		toplabs = range(0,21,4)
		toppos = range(0,141,28)
		r.axis(side=3, at=toppos, labels=toplabs, lwd=2, tck=-0.01)
		
		r.mtext(side=3, at=1, line=0, cex=0.4, text='M')
		r.mtext(side=3, at=3, line=0, cex=0.4, text='W')
		r.mtext(side=3, at=5, line=0, cex=0.4, text='F')
		r.mtext(side=3, at=7, line=0.5, cex=0.4, text='SUN', las=2)
		r.mtext(side=3, at=42, line=2, text='SUCCESSIVE')
		r.mtext(side=3, at=70, line=2, text='CALENDAR')
		r.mtext(side=3, at=98, line=2, text='WEEKS')
		r.mtext(side=3, line=4, cex=1.2, text=self.title)
		
		r.mtext(side=2, at=1000, line=4, text='COUNT PER DAY')
		
		r.mtext(side=1, line=2, text='SUCCESSIVE CALENDAR DAYS')
		
class WeeklyPerWeekChart(Chart):
	"""Weekly/Week Standard Celeration Chart."""
	
	def __init__(self, name='', x_start=0, x_end=100, period=5, cycles=6, cycle_start=0,
		cycle_end=6, fg='light blue', bg='white', clutter=4, format='pdf', outfile='figure',
		chart_type='weekly', title='WEEKLY per week CHART', debug=False):
		
		self.name=name
		self.x_start=x_start
		self.x_end=x_end
		self.period=period
		self.cycles=cycles
		self.cycle_start=cycle_start
		self.cycle_end=cycle_end
		self.fg=fg
		self.bg=bg
		self.clutter=clutter
		self.format=format
		self.outfile=outfile
		self.chart_type=chart_type
		self.title=title
		self.debug=debug
		self.objects={}
		
		self._build_y()
		self._build_x()

class MonthlyPerMonthChart(Chart):
	"""Monthly/Month Standard Celeration Chart."""
	
	def __init__(self, name='', x_start=0, x_end=120, period=6, cycles=6, cycle_start=0,
		cycle_end=6, fg='light blue', bg='white', clutter=4, format='pdf', outfile='figure',
		chart_type='monthly', title='MONTHLY per month CHART', debug=False):
		
		self.name=name
		self.x_start=x_start
		self.x_end=x_end
		self.period=period
		self.cycles=cycles
		self.cycle_start=cycle_start
		self.cycle_end=cycle_end
		self.fg=fg
		self.bg=bg
		self.clutter=clutter
		self.format=format
		self.outfile=outfile
		self.chart_type=chart_type
		self.title=title
		self.debug=debug
		self.objects={}
		
		self._build_y()
		self._build_x()
		
class ChartHandler(ContentHandler):
	"""SAX handler to process Chartshare XML files."""
	
	def __init__(self, outfile="figure%i"):
		ContentHandler.__init__(self)
		self.isChart = False
		self.isVector = False
		self.isElement = False
		self.isPhase = False
		self.chart_count=0
		self.vector_count=0
		self.phase_count=0
		self.out_format = outfile
		self.text=''
		
	def startElement(self, name, attrs):
		if (name == 'chart'):
			self.isChart=True
			self.chart_count+=1
			
			if (attrs.get('type') == 'daily'):
				self.root = DailyPerMinuteChart()
			elif (attrs.get('type') == 'yearly'):
				self.root = YearlyChart()
			elif (attrs.get('type') == 'dailyperday'):
				self.root = DailyPerDayChart()
			elif (attrs.get('type') == 'monthly'):
				self.root = MonthlyPerMonthyChart()
			elif (attrs.get('type') == 'weekly'):
				self.root = WeeklyPerWeekChart()
			else:
				self.root = Chart()
				### Insert logic for custom charts here
			
			if (attrs.get('name')):
				self.root.name = str(attrs.get('name'))
			else:
				self.root.name = (self.out_format % self.chart_count)
				
			if (attrs.get('outfile')):
				self.root.outfile = str(attrs.get('outfile'))
			else:
				self.root.outfile = (self.out_format % self.chart_count) + '.' + self.root.format
				
		elif (name == 'vector'):
			self.isVector = True
			self.vector_count+=1
			
			self.v = Vector(start=self.root.x_start, end=self.root.x_end)
			if (attrs.get('name')):
				self.v.name = str(attrs.get('name'))
			else:
				self.v.name = ("vector%i" % self.vector_count)
				
			if (attrs.get('linetype')):
				self.v.linetype=str(attrs.get('linetype'))
			if (attrs.get('color')):
				self.v.color=str(attrs.get('color'))
			if (attrs.get('symbol')):
				try:
					symbol=int(attrs.get('symbol'))
				except ValueError:
					symbol=str(attrs.get('symbol'))
				self.v.symbol=symbol
			if (attrs.get('continuous')):
				continuous = attrs.get('continuous')
				if (continuous.lower() == 'false'):
					self.v.continuous=False
				else:
					self.v.continuous=True
								
		elif (name == 'element'):
			self.isElement=True
			self.e = Element()
			try:
				self.e.offset=int(attrs.get('offset'))
			except ValueError:
				raise OffsetTypeError, 'Offset attribute must be an integer'
			
		elif (name == 'phase'):
			self.isPhase = True
			self.p = Phase()
			self.phase_count+=1
			
			if (attrs.get('name')):
				self.p.name = attrs.get('name')
			else:
				self.p.name = ("phase%i" % self.phase_count)
				
			if (attrs.get('absolute_length') and attrs.get('length')):
				raise LengthConflict, 'A Phase cannot have both a length and absolute_length attribute.'
				
			if (attrs.get('pos')):
				try:
					self.p.pos = float(attrs.get('pos'))
				except ValueError:
					raise OffsetTypeError, 'Phase position must be a valid number.'
			else:
				raise RequiredAttribute, "A Phase change line must have a 'pos' attribute."
			
			if (attrs.get('absolute_length')):
				try:
					self.p.absolute_length = float(attrs.get('absolute_length'))
				except ValueError:
					raise LengthTypeError, 'absolute_length must be a vaild number.'
			
			if (attrs.get('length')):
				try:
					self.p.length = float(attrs.get('length'))
				except ValueError:
					raise LengthTypeError, 'length must be a valid number.'
			
			if (attrs.get('color')):
				self.p.color = str(attrs.get('color'))
			
			if (attrs.get('width')):
				try:
					self.p.width = int(attrs.get('width'))
				except ValueError:
					raise LengthTypeError, 'width must be an integer.'
			
			if (attrs.get('tail_length')):
				try:
					self.p.tail_length=float(attrs.get('tail_length'))
				except ValueError:
					raise LengthTypeError, 'tail_length must be a vaild number.'
			
	def characters(self, content):
		self.text += str(content)

	def endElement(self, name):
		if (name == 'chart'):
			self.isChart=False

		elif (name == 'vector'):
			self.isVector = False
			try:
				self.root.objects[self.v.name]=self.v
			except NameError:
				raise ObjectOutOfContext, 'Vectors must be part of a chart.  Chart object does not exist.'
			del(self.v)
			
		elif (name == 'element'):
			self.isElement = False
			
			try:
				self.v.elements[self.e.offset]=float(self.text)
			except ValueError:
				raise OffsetTypeError, 'Offset value must be a number. Value Passed: %s' % self.text
			except NameError:
				raise ObjectOutOfContext, 'Elements must be part of a vector.  Vector object not found.'
			del(self.e)
			self.text=''
			
		elif (name == 'phase'):
			self.isPhase = False
			self.p.label = str(self.text)
			self.p.label = self.p.label.strip()
			
			try:
				self.root.objects[self.p.name]=self.p
			except NameError:
				raise ObjectOutOfContext, 'Vectors must be part of a chart.  Chart object not found.'
			del(self.p)
			self.text=''
			
	def get_chart(self):
		return self.root

class ChartFactory(object):
	""" The ChartFactory object creates Chart objects from chartshare data sources."""

	def __init__(self):
		self.saxparser = make_parser()
		self.handler = ChartHandler()
		self.saxparser.setContentHandler(self.handler)
		
	def parse(self, xml):
		"""Parses an xml string and returns a Chart object."""
		self.saxparser.parse(xml)
		return self.handler.get_chart()

class SymbolOutOfRange(Exception):
    """Symbol out of Range."""
    
class InvalidLinetype(Exception):
	"""Invalid Line Type"""

class ObjectHasNoName(Exception):
	"""Chart, Vector, and Phase objects must have names."""
		
class LengthConflict(Exception):
	"""A Phase change line can only have an absolute length or a relative length."""
		
class LengthTypeError(Exception):
	"""Length must be a valid number."""
		
class OffsetTypeError(Exception):
	"""An element offset must be an integer."""
		
class ObjectOutOfContext(Exception):
	"""Object must be contained within another object."""
