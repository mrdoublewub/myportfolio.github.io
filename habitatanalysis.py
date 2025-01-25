#If I ever come back to this I think I can simplify the parameters somehow. I know a GPT told me a simpler way to organize things that I need to look over. Also, need to review python toolbox creation and code probably to make tool most effective. See 'better script' for example.
import os
import gc
import arcpy
import tempfile
from arcpy.sa import *

#Input Data
county=arcpy.GetParameterAsText(0)
road=arcpy.GetParameterAsText(1)
raster=arcpy.GetParameterAsText(2)

#Step 1 parameters
county_field=arcpy.GetParameterAsText(3)
county_inequality=arcpy.GetParameterAsText(4)
county_type=arcpy.GetParameterAsText(5)
county_clause=f"{county_field}{county_inequality}'{county_type}'"

#Step 2 parameters
output_measurement=arcpy.GetParameterAsText(6)

#Step 3 parameters
reclass_field=arcpy.GetParameterAsText(7)
start=arcpy.GetParameter(8)
end=arcpy.GetParameter(9)
new=arcpy.GetParameter(10)
missing_values=arcpy.GetParameterAsText(11)
#setlist=[[start,end,new]]
reclass_field=reclass_field.upper()
reclass_value=RemapRange([[float(start),float(end),float(new)]])
missing_values=missing_values.upper()

#Step 4 parameters
simplify=arcpy.GetParameter(12)
simplify='SIMPLIFY' if simplify else 'NO_SIMPLIFY'

#Step 5 parameters
overlap_type=arcpy.GetParameterAsText(13)
distance=arcpy.GetParameter(14)
unit=arcpy.GetParameterAsText(15)
selection_type=arcpy.GetParameterAsText(16)
overlap_type=overlap_type.upper()
unit=unit.capitalize()
search_distance=f"{distance} {unit}"
selection_type=selection_type.upper()

#Step 6 parameters
overlap_type2=arcpy.GetParameterAsText(17)
distance2=arcpy.GetParameter(18)
unit2=arcpy.GetParameterAsText(19)
selection_type2=arcpy.GetParameterAsText(20)
invert_spatial_relationship=arcpy.GetParameterAsText(21)
overlap_type2=overlap_type2.upper()
unit2=unit2.capitalize()
search_distance2=f"{distance2} {unit2}"
selection_type2=selection_type2.upper()
invert_spatial_relationship=invert_spatial_relationship.upper()

#Step 7 parameters
field_name=arcpy.GetParameterAsText(22)
field_property=arcpy.GetParameterAsText(23)
area_unit=arcpy.GetParameterAsText(24)
final_field=arcpy.GetParameterAsText(25)
final_inequality=arcpy.GetParameterAsText(26)
final_size=arcpy.GetParameter(27)
field_property=field_property.upper()
field_list=[[field_name,field_property]]
area_unit=area_unit.upper()
final_clause=f"{final_field}{final_inequality}{final_size}"

#Output
final=arcpy.GetParameterAsText(28)

#Temporary Files
temp=tempfile.gettempdir()
temp_files={
    'temp1':os.path.join(temp,'1.shp'),
    'temp2':os.path.join(temp,'2.tif'),
    'temp3':os.path.join(temp,'3.tif'),
    'temp4':os.path.join(temp,'4.shp'),
    'temp5':os.path.join(temp,'5.shp'),
    'temp6':os.path.join(temp,'6.shp')
}

#True script:
try:
    #Check Spatial Analyst extension, it is necessary to move forward.
    if arcpy.CheckExtension('Spatial')=='Available':
        arcpy.CheckOutExtension('Spatial')
    else:
        raise RuntimeError('Spatial Analyst Extension is unavailable.')

    #Step 1: Subset Coasts
    arcpy.AddMessage('Analyzing Coasts...')
    try:
        arcpy.analysis.Select(county,temp_files['temp1'],county_clause)
        arcpy.AddMessage('Step 1/7 Complete')
    except arcpy.ExecuteError:
        arcpy.AddError('County coastline selection failed.')
        arcpy.AddError(arcpy.GetMessages())
        raise

    #Step 2: Calculate Slope
    arcpy.AddMessage('Calculating slopes...')
    try:
        temp2=Slope(raster,output_measurement)
        temp2.save(temp_files['temp2'])
        arcpy.AddMessage('Step 2/7 Complete')
    except arcpy.ExecuteError:
        arcpy.AddError('Slope tool failed.')
        arcpy.AddError(arcpy.GetMessages())
        raise

    #Step 3: Reclassify
    arcpy.AddMessage('Reclassifying...')
    try:
        temp3=Reclassify(temp2,reclass_field,reclass_value,missing_values)
        temp3.save(temp_files['temp3'])
        arcpy.AddMessage('Step 3/7 Complete')
    except arcpy.ExecuteError:
        arcpy.AddError('Reclassify tool failed')
        arcpy.AddError(f'Reclassify parameters: {reclass_field}, {reclass_value}, {missing_values}')
        arcpy.AddError(arcpy.GetMessages())
        raise

    #Step 4: Convert to Polygons
    arcpy.AddMessage('Converting to polygons...')
    try:
        arcpy.conversion.RasterToPolygon(temp3, temp_files['temp4'],simplify)
        arcpy.AddMessage('Step 4/7 Complete')
    except arcpy.ExecuteError:
        arcpy.AddError('Raster to Polygon tool failed.')
        arcpy.AddError(arcpy.GetMessages())
        raise

    #Step 5: Distance to Coast
    arcpy.AddMessage('Isolating distance to coast...')
    try:
        coast_layer=arcpy.management.MakeFeatureLayer(temp_files['temp4'],'coast_layer')
        arcpy.management.SelectLayerByLocation(coast_layer,overlap_type,temp_files['temp1'],search_distance,selection_type)
        arcpy.management.CopyFeatures(coast_layer,temp_files['temp5'])
        arcpy.management.Delete(coast_layer)
        arcpy.AddMessage('Step 5/7 Complete')
    except arcpy.ExecuteError:
        arcpy.AddError('Select polygons near coast failed.')
        arcpy.AddError(arcpy.GetMessages())
        raise

    #Step 6: Distance to Roads
    arcpy.AddMessage('Isolating distance to roads...')
    try:
        roads_layer=arcpy.management.MakeFeatureLayer(temp_files['temp5'],'roads_layer')
        arcpy.management.SelectLayerByLocation(roads_layer,overlap_type2,road,search_distance2,selection_type2,invert_spatial_relationship)
        arcpy.management.CopyFeatures(roads_layer,temp_files['temp6'])
        arcpy.management.Delete(roads_layer)
        arcpy.AddMessage('Step 6/7 Complete')
    except arcpy.ExecuteError:
        arcpy.AddError('Select polygons not-near roads failed.')
        arcpy.AddError(arcpy.GetMessages())
        raise

    #Step 7: Final Selection
    arcpy.AddMessage('Calculating area...')
    try:
        arcpy.management.CalculateGeometryAttributes(temp_files['temp6'],field_list,area_unit=area_unit)
    except arcpy.ExecuteError:
        arcpy.AddError('Calculate Geometry failed.')
        arcpy.AddError(arcpy.GetMessages())
        raise
    arcpy.AddMessage('Making final selection...')
    try:
        arcpy.analysis.Select(temp_files['temp6'],final,final_clause)
        arcpy.AddMessage('Step 7/7 Complete')
    except arcpy.ExecuteError:
        arcpy.AddError('Large habitat selection failed.')
        arcpy.AddError(arcpy.GetMessages())
        raise

#If a runtime error occurs cancel script
except RuntimeError as e:
    arcpy.AddError(f'Error: {e}')
    raise SystemExit('Exiting script due to runtime error.')

#If an exception error occurs cancel script
except Exception as e:
    arcpy.AddError(f"Error: {e}")
    raise SystemExit('Exiting script due to general error.')

finally:
    #Cleanup Section
    arcpy.AddMessage('Cleaning up temporary files...')
    try:
        for x in temp_files.values():
            if os.path.exists(x):
                del x
    
        #Check in extensions
        arcpy.CheckInExtension('Spatial')
        gc.collect()

    except Exception as e:
        arcpy.AddError(f'Could not clean up: {e}')

    arcpy.AddMessage('Done!')

