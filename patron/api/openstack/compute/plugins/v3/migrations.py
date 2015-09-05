#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from patron.api.openstack import extensions
from patron.api.openstack import wsgi
from patron import compute
from patron.objects import base as obj_base


ALIAS = "os-migrations"


def authorize(context, action_name):
    extensions.os_compute_authorizer(ALIAS)(context, action=action_name)


def output(migrations_obj):
    """Returns the desired output of the API from an object.

    From a MigrationsList's object this method returns a list of
    primitive objects with the only necessary fields.
    """
    objects = obj_base.obj_to_primitive(migrations_obj)
    for obj in objects:
        del obj['deleted']
        del obj['deleted_at']
    return objects


class MigrationsController(wsgi.Controller):
    """Controller for accessing migrations in OpenStack API."""
    def __init__(self):
        self.compute_api = compute.API()

    @extensions.expected_errors(())
    def index(self, req):
        """Return all migrations in progress."""
        context = req.environ['patron.context']
        authorize(context, "index")
        migrations = self.compute_api.get_migrations(context, req.GET)
        return {'migrations': output(migrations)}


class Migrations(extensions.V3APIExtensionBase):
    """Provide data on migrations."""
    name = "Migrations"
    alias = ALIAS
    version = 1

    def get_resources(self):
        resources = []
        resource = extensions.ResourceExtension(ALIAS,
                                                MigrationsController())
        resources.append(resource)
        return resources

    def get_controller_extensions(self):
        return []