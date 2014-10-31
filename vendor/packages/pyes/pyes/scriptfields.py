#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Armando Guereca'

class ScriptFields:
    _internal_name = "script_fields"
    """
    This object create the script_fields definition
    """
    def __init__(self, field_name, script, params = None):
        self.fields={}
        self.add_field(field_name, script, params or {})
    
    def add_field(self, field_name, script, params = None):
        """
        Add a field to script_fields
        """
        data = {}
        if script:
            data['script'] = script
        else:
            raise ScriptFieldsError("Script is required for script_fields definition")
        if params:
            if isinstance(params, dict):
                if len(params):
                    data['params'] = params
            else:
                raise ScriptFieldsError("Parameters should be a valid dictionary")        
                
        self.fields[field_name] = data
    
    def add_parameter(self, field_name, param_name, param_value):
        """
        Add a parameter to a field into script_fields
        
        The ScriptFields object will be returned, so calls to this can be chained.
        """
        try:
            self.fields[field_name]['params'][param_name] = param_value
        except Exception as ex:
            raise ScriptFieldsError("Error adding parameter %s with value %s :%s" % (param_name,param_value,ex))
        
        return self

    def serialize(self):       
        return self.fields
