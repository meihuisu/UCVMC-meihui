##
#  @file elevation_profile.py
#  @brief Plots a 1D elevation profile to an image or a pre-existing plot.
#  @author 
#  @version 14.7.0
#
#  Allows for generation of a 1D elevation profile, either interactively, via
#  arguments, or through Python code in the class ElevationProfile.

#  Imports
from common import Plot, Point, MaterialProperties, UCVM, UCVM_CVMS, plt
from scipy.interpolate import spline, splprep, splev
from scipy.interpolate import Rbf, InterpolatedUnivariateSpline
import scipy.interpolate as interpolate
import numpy as np
import pdb
import json

##
#  @class ElevationProfile
#  @brief Plots a 1D elevation profile at a given @link common.Point Point @endlink.
#
#  Generates a 1D elevation profile that can either be saved as a file or displayed
#  to the user. 
class ElevationProfile:
    
    ##
    #  Initializes the 1D profile class.
    #
    #  @param startingpoint The @link common.Point starting point @endlink from which this plot should start.
    #  @param toend The ending elevation, in meters, where this plot should end.
    #  @param spacing The discretization interval in meters.
    #  @param cvm The CVM from which to retrieve these material properties.
    def __init__(self, startingpoint, toelevation, spacing, cvm, threshold = None):
        if not isinstance(startingpoint, Point):
            raise TypeError("The starting point must be an instance of Point.")
        else:
            ## Defines the @link common.Point starting point @endlink for the elevation profile.
            self.startingpoint = startingpoint
        
        if (toelevation - self.startingpoint.elevation) % spacing != 0:
            raise ValueError("%s\n%s\n%s" % ("The spacing value does not divide evenly into the requested elevation. ", \
                          "Please make sure that the elevation (%.2f - %.2f) divided by the spacing " % (toelevation, self.startingpoint.elevation), \
                          "%.2f has no remainder" % (spacing)))
        else:
            ## Defines the elevation to which the plot should go in meters.
            self.toelevation = toelevation
            self.startelevation = self.startingpoint.elevation
            
        ## The discretization of the plot, in meters.
        self.spacing = spacing
        
        ## The CVM to use (must be installed with UCVM).
        self.cvm = cvm

        ## Private holding place for returned Vp data.        
        self.vplist = []
        ## Private holding place for returned Vs data.
        self.vslist = []
        ## Private holding place for returned density data.
        self.rholist = []

        ## Private holding place for elevation data.
        self.elevationlist = []

        ## Default threshold in simplified units
        self.threshold = threshold
    
    ## 
    #  Generates the elevation profile in a format that is ready to plot.
    def getplotvals(self, properties=None, meta = {}):
        
        point_list = []

        datafile = None
        if 'datafile' in meta :
            datafile = meta['datafile']

        filename = None
        if 'outfile' in meta :
           filename = meta['outfile']
        
        # Generate the list of points.
 
        toto=self.toelevation
        if(toto <=0 ):
          toto = toto-1
        else:
          toto = toto+1

        for i in np.arange(self.startelevation, toto, self.spacing):
            point_list.append(Point(self.startingpoint.longitude, self.startingpoint.latitude, elevation=i))
            

        u = UCVM()
###MEI
        if (datafile != None) :
            print "\nUsing --> "+datafile
            data = u.import_matprops(datafile)
        else:
            data = u.query(point_list, self.cvm, elevation=1)
        
        tmp = []
        for matprop in data:
            self.vplist.append(float(matprop.vp) / 1000)
            self.vslist.append(float(matprop.vs) / 1000)
            self.rholist.append(float(matprop.density) / 1000)
## create the blob
            if(datafile == None) : ## save an external copy of matprops 
              b= { 'vp':float(matprop.vp), 'vs':float(matprop.vs), 'density':float(matprop.density) }
              tmp.append(b)

        if(datafile == None) :
              blob = json.dumps({ 'matprops' : tmp })
              u.export_matprops(blob,filename)
              u.export_metadata(meta,filename)
    
    ##
    #  Adds the elevation profile to a pre-existing plot.
    #
    #  @param plot The @link common.Plot Plot @endlink object to which we're plotting.
    #  @param properties An array of properties to plot. Can be vs, vp, or density.
    #  @param colors The colors that the properties should be plotted as. Optional.
    #  @param customlabels An associated array of labels to put for the legend. Optional.
    def addtoplot(self, plot, properties, colors = None, customlabels = None, meta = {}):
        
        # Check that plot is a Plot
        if not isinstance(plot, Plot):
            raise TypeError("Plot must be an instance of the class Plot.")
        
        # Get the material properties.
        self.getplotvals(properties = properties, meta = meta)
        
        max_x = 0
        yvals = []

        toto=self.toelevation
        if(toto <= 0):
          toto=toto-1
        else:
          toto=toto+1

        for i in xrange(int(self.startelevation), int(toto), int(self.spacing)):  
            yvals.append(i)       
        
        if customlabels != None and "vp" in properties: 
            vplabel = customlabels["vp"]
        else:
            vplabel = "Vp (km/s)" 
        
        if customlabels != None and "vs" in properties: 
            vslabel = customlabels["vs"]
        else:
            vslabel = "Vs (km/s)"  
        
        if customlabels != None and "density" in properties: 
            densitylabel = customlabels["density"]
        else:
            densitylabel = "Density (g/cm^3)"  

        if colors != None and "vp" in properties: 
            vpcolor = colors["vp"]
        else:
            vpcolor = "r" 
        
        if colors != None and "vs" in properties: 
            vscolor = colors["vs"]
        else:
            vscolor = "b"  
        
        if colors != None and "density" in properties: 
            densitycolor = colors["density"]
        else:
            densitycolor = "g"                
        
        if "vp" in properties:
            max_x = max(max_x, max(self.vplist))
            plot.addsubplot().plot(self.vplist, yvals, "-", color=vpcolor, label=vplabel)
        if "vs" in properties:
            max_x = max(max_x, max(self.vslist))
            plot.addsubplot().plot(self.vslist, yvals, "-", color=vscolor, label=vslabel)

## attempted to draw a smoothed line, not good
##            xs=np.array(self.vslist)
##            ys=np.array(yvals)
##            # spline parameters
##            s=3.0 # smoothness parameter
##            k=2 # spline order
##            nest=-1 # estimate of number of knots needed (-1 = maximal)
##            # find the knot points
##            tckp,u = splprep([xs,ys],s=s,k=k,nest=nest)
##            # evaluate spline, including interpolated points
##            newx,newy = splev(np.linspace(0,1,500),tckp)
##            plot.addsubplot().plot(newx, newy, "b-", label="smoothed"+vslabel)
            ## add a vline if there is a vs threshold
            if self.threshold != None : 
                plot.addsubplot().axvline(self.threshold/1000, color='k', linestyle='dashed')

        self.elevationlist=yvals

        if "density" in properties:
            max_x = max(max_x, max(self.rholist))
            plot.addsubplot().plot(self.rholist, yvals, "-", color=densitycolor, label=densitylabel) 
        
        plt.legend(loc="lower left")
                
        if plt.ylim()[0] < plt.ylim()[1]:
            plt.gca().invert_yaxis() 
        
        if max_x > plt.xlim()[1]:
            plt.xlim(0, math.ceil(max_x / 0.5) * 0.5)

        plt.axis([0, max_x, int(self.toelevation), int(self.startelevation)])
    
    ##
    #  Plots a new elevation profile using all the default plotting options.
    #
    #  @param properties An array of material properties. Can be one or more of vp, vs, and/or density.
    #  @param filename If this is set, the plot will not be shown but rather saved to this location.
    def plot(self, properties, meta = {}):

        if self.startingpoint.description == None:
            location_text = ""
        else:
            location_text = self.startingpoint.description + " "

        # Gets the better CVM description if it exists.
        try:
            cvmdesc = UCVM_CVMS[self.cvm]
        except: 
            cvmdesc = self.cvm

        # Call the plot object.
        p = Plot("%s%s Elevation Profile From %sm To %sm at (%.2f,%.2f)" % (location_text, cvmdesc, self.startelevation, self.toelevation, self.startingpoint.longitude, self.startingpoint.latitude), \
                 "Units (see legend)", "Elevation (m)", None, 7, 10)

        # Add to plot.
        self.addtoplot(p, properties, meta=meta)

        filename = None
        if 'outfile' in meta :
           filename = meta['outfile']

        if filename == None:
            plt.show()
        else:
            plt.savefig(filename)
