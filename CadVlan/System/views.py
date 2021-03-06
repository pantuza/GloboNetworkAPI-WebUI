# -*- coding:utf-8 -*-

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from CadVlan.Util.converters.util import split_to_array
from CadVlan.Util.Decorators import log, login_required, has_perm, has_perm_external
from CadVlan.templates import VARIABLES_FORM, VARIABLES_LIST, VARIABLES_EDIT
from django.shortcuts import render_to_response, redirect, render
from django.template.context import RequestContext
from CadVlan.Auth.AuthSession import AuthSession
from networkapiclient.exception import NetworkAPIClientError
from django.contrib import messages
from CadVlan.messages import error_messages, system_variable_messages
from CadVlan.permissions import ADMINISTRATION, EQUIPMENT_MANAGEMENT
from CadVlan.forms import DeleteForm
from CadVlan.System.facade import *
from CadVlan.System.forms import VariableForm
from networkapiclient.exception import VariableError


logger = logging.getLogger(__name__)

@log
@login_required
@has_perm([
    {"permission": EQUIPMENT_MANAGEMENT, "read": True },
    {"permission": EQUIPMENT_MANAGEMENT, "write": True}
])
def add_variable(request):

    try:
        # Get user
        auth = AuthSession(request.session)
        client = auth.get_clientFactory()

        lists = dict()

        if request.method == 'GET':
            form = VariableForm()
            lists['form'] = form

        if request.method == 'POST':
            form = VariableForm(request.POST)
            lists['form'] = form

            if form.is_valid():
                name = request.POST.get('name')
                value = request.POST.get('value')
                description = request.POST.get('description')

                create_new_variable(client, name, value, description)
                messages.add_message(request, messages.SUCCESS, system_variable_messages.get('success_insert'))

                return redirect('variables.list')

    except NetworkAPIClientError, e:
        logger.error(e)
        messages.add_message(request, messages.ERROR, e)
        return render_to_response(VARIABLES_FORM, lists, context_instance=RequestContext(request))

    return render_to_response(VARIABLES_FORM, lists, context_instance=RequestContext(request))

@log
@login_required
@has_perm([
    {"permission": EQUIPMENT_MANAGEMENT, "read": True },
    {"permission": EQUIPMENT_MANAGEMENT, "write": True}
])
def edit_variable(request, variable_id):

    try:
        # Get user
        auth = AuthSession(request.session)
        client = auth.get_clientFactory()

        lists = dict()

        if request.method == 'GET':
            #variable = get_variable(client, variable_id)
            variable = {'name': "laura", 'value': "value", 'description': variable_id}
            form = VariableForm(initial={'name': variable.get('name'), 'value': variable.get('value'),
                                         'description': variable.get('description')})

        if request.method == 'POST':
            form = VariableForm(request.POST)

            if form.is_valid():
                name = request.POST.getlist('name')
                value = request.POST.getlist('value')
                description = request.POST.getlist('description')

                #update_variable(client,name, value, description)
                messages.add_message(request, messages.SUCCESS, system_variable_messages.get('success_update'))

                #return redirect('pool.list')

        lists['form'] = form

    except NetworkAPIClientError, e:
        logger.error(e)
        messages.add_message(request, messages.ERROR, e)

    return render_to_response(VARIABLES_EDIT, lists, context_instance=RequestContext(request))

@log
@login_required
@has_perm([
    {"permission": EQUIPMENT_MANAGEMENT, "read": True },
    {"permission": EQUIPMENT_MANAGEMENT, "write": True}
])
def list_variables(request):

    try:
        # Get user
        auth = AuthSession(request.session)
        client = auth.get_clientFactory()

        lists = dict()

        if request.method == 'GET':
            lists['variables'] = list_all_variables(client)
            lists['delete_form'] = DeleteForm()

    except NetworkAPIClientError, e:
        logger.error(e)
        messages.add_message(request, messages.ERROR, e)

    return render_to_response(VARIABLES_LIST, lists, context_instance=RequestContext(request))

@log
@login_required
@has_perm([{"permission": EQUIPMENT_MANAGEMENT, "write": True}
])
def delete_all(request):

    if request.method == 'POST':

        form = DeleteForm(request.POST)

        if form.is_valid():
            auth = AuthSession(request.session)
            client = auth.get_clientFactory()

            ids = split_to_array(form.cleaned_data['ids'])

            error_list = list()
            have_errors = False

            for id_var in ids:
                try:
                    client.create_system().delete_all(id_var)
                except VariableError:
                    error_list.append(id_var)
                except NetworkAPIClientError, e:
                    logger.error(e)
                    messages.add_message(request, messages.ERROR, e)
                    have_errors = True
                    break

            if len(error_list) == len(ids):
                messages.add_message(request, messages.ERROR, error_messages.get("can_not_remove_all"))
            elif len(error_list) > 0:
                msg = ""
                for id_error in error_list:
                    msg = msg + id_error + ", "
                msg = error_messages.get("can_not_remove") % msg[:-2]
                messages.add_message(request, messages.WARNING, msg)
            elif have_errors == False:
                messages.add_message(request, messages.SUCCESS, system_variable_messages.get("success_delete"))
            else:
                messages.add_message(request, messages.SUCCESS, error_messages.get("can_not_remove_error"))

        else:
            messages.add_message(request, messages.ERROR, error_messages.get("select_one"))

    # Redirect to list_all action
    return redirect("variables.list")