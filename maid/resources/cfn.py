# Copyright 2016 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import itertools
import logging

from maid.actions import ActionRegistry, BaseAction
from maid.filters import FilterRegistry

from maid.manager import ResourceManager, resources
from maid.utils import local_session, type_schema


log = logging.getLogger('maid.cfn')

filters = FilterRegistry('cfn.filters')
actions = ActionRegistry('cfn.actions')


@resources.register('cfn')
class CloudFormation(ResourceManager):

    action_registry = actions
    filter_registry = filters

    def resources(self):
        c = self.session_factory().client('cloudformation')
        self.log.info("Querying cloudformation")
        p = c.get_paginator('describe_stacks')
        results = p.paginate()
        stacks = list(itertools.chain(*[rp['Stacks'] for rp in results]))
        return self.filter_resources(stacks)


@actions.register('delete')
class Delete(BaseAction):

    schema = type_schema('delete')

    def process(self, stacks):
        with self.executor_factory(max_workers=10) as w:
            list(w.map(self.process_stack, stacks))

    def process_stacks(self, stack):
        client = local_session(
            self.manager.session_factory).client('cloudformation')
        client.delete_stack(StackName=stack['StackName'])

