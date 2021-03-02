
from PyQt5.QtCore import *
from kelebek_conf import *
from kelebek_node_base import *
from nodeeditor.utils import dumpException

from spider.kelebek_node_functions import get_item, get_all, multi_link, paginator, broadcast, coroutine
from kelebek_multithreading import run_threaded_process, run_simple_thread


import time
import os
from colorama import Fore

import asyncio
from requests import Session
from concurrent.futures import Future

DEBUG = True


# page_url = 'http://books.toscrape.com/'
# pagination_path = '//a[text()="next"]/@href'
# multi_title_path = '//h3/a/@href'

price_path = '//div[1]/div[2]/p[normalize-space(@class)="price_color"]/text()'
title_path = '//h1/text()'


@register_node(OP_NODE_HOP_LINK)
class KelebekNodeHopLink(KelebekNode):
    # icon = "icons/sub.png"
    op_code = OP_NODE_HOP_LINK
    op_title = "Hop Link"
    content_label = ""
    content_label_objname = "Kelebek_node_hop_link"

    def evalOperation(self, input1, value1):
        print("NOT IMPLEMENTED")


@register_node(OP_NODE_PAGINATION)
class KelebekNodePagination(KelebekNode):
    # icon = "icons/add.png"
    op_code = OP_NODE_PAGINATION
    op_title = "Pagination"
    content_label = ""
    content_label_objname = "Kelebek_node_pagination"

    def __init__(self, scene):
        super().__init__(scene, inputs=[2], outputs=[1])

    #     self.fut = Future()
    #
    # def finished(self, result):
    #     self.running_thread = True
    #     self.fut.set_result(result)
    #     # need to communicate that the operating has completed to descendants
    #     print("THREAD FINISHED: ", result)

    def pagination(self, input1_page, value1_pagination_path: str):
        output = []
        print(Fore.CYAN, 'INPUT PAGE:', input1_page, flush=True)
        with Session() as client:
            for response in paginator(client, input1_page, value1_pagination_path, output):
                # time.sleep(1)
                pass
            client.close()
        return output

    def evalOperation(self, input1_page, value1_pagination_path: str):
        x = self.pagination(input1_page, value1_pagination_path)
        return x
        # should have this like what it was previously.
        # run_simple_thread(self.pagination, self.finished, input1_page, value1_pagination_path)
        # return self.fut


@register_node(OP_NODE_HOP_ALL_LINKS)
class KelebekNodeHopAllLinks(KelebekNode):
    # icon = "icons/divide.png"
    op_code = OP_NODE_HOP_ALL_LINKS
    op_title = "Hop All Links"
    content_label = ""
    content_label_objname = "Kelebek_hop_all_links"

    def evalOperation(self, gen, path):
        #  if input if is future --> wait_for, wrap_future
        if isinstance(gen, Future):
            gen = gen.result()

        # This does not work with qt threads
        # loop = asyncio.get_event_loop()
        # x = loop.run_until_complete(multi_link(loop, gen, path))

        # call_soon(), call_later() or call_at()  --> these are not thread safe
        # run_coroutine_threadsafe -- for async coros only
        # call_soon_threadsafe --> for non async functions
        # asyncio.get_running_loop()

        # This works with qt threads but freezes sometimes.
        new_loop = asyncio.new_event_loop()
        x = new_loop.run_until_complete(multi_link(new_loop, gen, path))

        # does the event loop close itself?
        # also this shit is using massive amounts of memory
        self.running_thread = True
        return x


@register_node(OP_NODE_SINGLE_ITEM)
class KelebekNodeSingleItem(KelebekNode):
    # icon = "icons/sub.png"
    op_code = OP_NODE_SINGLE_ITEM
    op_title = "Get Item"
    content_label = ""
    content_label_objname = "Kelebek_node_single_item"

    def evalOperation(self, input1, value1):
        items = []
        for i in input1:
            item = get_item(i, value1)
            print(Fore.BLUE, 'ITEM: ', item)
            items.append(item)
        self.running_thread = True
        return items

        # output_nodes = self.getOutputs()
        # broadcaster = broadcast(output_nodes)
        # while True:
        #     data = yield

        # for i in input1:
        #     print(type(i))
        #     yield from get_item(i, value1)


@register_node(OP_NODE_MULTI_ITEM)
class KelebekNodeMultiItem(KelebekNode):
    # icon = "icons/sub.png"
    op_code = OP_NODE_MULTI_ITEM
    op_title = "Get All"
    content_label = ""
    content_label_objname = "Kelebek_node_multi_item"

    def get_all_items(self, input1, value1):
        if isinstance(input1, Future):
            input1 = input1.result()
            print('input is a future')

        output = []
        for i in input1:
            output.append(get_all(i, value1))
        self.running_thread = True
        return output

    def evalOperation(self, input1, value1):
        return self.get_all_items(input1, value1)

        # output=[]
        # for i in input1:
        #     print(type(i))
        #     output.append(get_all(i, value1))
        # return output

        # This for iterating through TEST NODE one by one
        # for i in input1:
        #     items = get_all(i, value1)
        #     yield items

        # for i in input1:
        #     print(type(i))
        #     yield from get_all(i, value1)


@register_node(OP_NODE_DISPLAY_OUTPUT)
class KelebekNodeDisplayOutput(KelebekNode):
    # icon = "icons/sub.png"
    op_code = OP_NODE_DISPLAY_OUTPUT
    op_title = "Display Output"
    content_label = ""
    content_label_objname = "Kelebek_node_display_output"

    def initInnerClasses(self):
        self.content = KelebekOutputDisplayContent(self)
        self.grNode = KelebekDisplayGraphicsNode(self)
        # self.content.edit.textChanged.connect(self.onInputChanged)

    def initSettings(self):
        super().initSettings()
        self.input_socket_position = LEFT_CENTER
        self.output_socket_position = RIGHT_CENTER
        self.input_multi_edged = True
        self.output_multi_edged = True

    def evalOperation(self, *args):
        print(Fore.LIGHTBLACK_EX, 'OUTPUT ARGS: ', *args, flush=True)
        self.running_thread = True
        return 'DISPLAY NODE ARGS: '+str(args)

    def evalImplementation(self):
        all_inputs_nodes = self.getInputs()

        print(Fore.BLUE, 'ALL INPUT NODES: ', all_inputs_nodes, flush=True)

        if not all_inputs_nodes:
            self.markInvalid()
            self.markDescendantsDirty()
            self.grNode.setToolTip("Connect all inputs")
            return None

        else:
            val = self.evalOperation(*(node.eval() for node in all_inputs_nodes))

            self.value = val

            self.content.text_edit.setPlainText("%s" % val)
            self.markDirty(False)
            self.markInvalid(False)
            self.grNode.setToolTip("")

            self.markDescendantsDirty()
            self.evalChildren()

            return val


@register_node(OP_NODE_TEST)
class KelebekTestNode(KelebekNode):
    op_code = OP_NODE_TEST
    op_title = "Test Node"
    content_label = ""
    content_label_objname = "Kelebek_node_test"

    def __init__(self, scene):
        super().__init__(scene, inputs=[1], outputs=[])

    def initSettings(self):
        super().initSettings()
        self.input_socket_position = LEFT_CENTER
        self.output_socket_position = RIGHT_CENTER
        self.input_multi_edged = True
        self.output_multi_edged = True

    def initInnerClasses(self):
        self.content = KelebekTestNodeContent(self)
        self.grNode = KelebekGraphicsNode(self)
        self.content.run_nodes.clicked.connect(self.clk_btn)

    # def flatten(self, curr_item, output):
    #     import types
    #     if isinstance(curr_item, types.GeneratorType):
    #         for item in curr_item:
    #             self.flatten(item, output)
    #     else:
    #         output.append(curr_item)

    def clk_btn(self):
        # val = self.evalImplementation()
        # print(val)
        all_inputs_nodes = self.getInputs()
        val = self.evalOperation(*(node.eval() for node in all_inputs_nodes))
        self.value = val
        self.eval()

    def evalOperation(self, *args):
        for arg in args:
            if isinstance(arg, Future):
                arg = arg.result()
            print(Fore.GREEN, 'ARG LENGTH: ', len(arg))
            print(Fore.GREEN, 'ARG: ', arg)
        x = [i for i in args]
        # print(x)
        return x

    def evalImplementation(self):
        all_inputs_nodes = self.getInputs()
        if not all_inputs_nodes:
            self.grNode.setToolTip("Input is not connected")
            self.markInvalid()
            return

        # val = self.evalOperation(*(node.eval() for node in all_inputs_nodes))

        if self.value is None:
            self.grNode.setToolTip("Input is NaN")
            self.markInvalid()
            return

        # self.value = val
        self.markInvalid(False)
        self.markDirty(False)
        self.grNode.setToolTip("")

        return self.value


class KelebekTestNodeContent(QDMNodeContentWidget):
    def initUI(self):
        self.contentlayout = QFormLayout(self)
        self.run_nodes = QPushButton(QIcon(os.path.join('images', 'play-hot.png')), 'Run', self)
        self.contentlayout.addWidget(self.run_nodes)


class KelebekOutputDisplayContent(QDMNodeContentWidget):
    def initUI(self):
        self.display_layout = QVBoxLayout(self)
        self.text_edit = QPlainTextEdit('Placeholder text')
        self.text_edit.setStyleSheet("QPlainTextEdit {color: white}")
        self.text_edit.setFixedSize(200*2, 60*2)
        self.display_layout.addWidget(self.text_edit, alignment=Qt.AlignCenter)


class KelebekDisplayGraphicsNode(KelebekGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.width = 220*2
        self.height = 85*2
        self.edge_roundness = 6
        self.edge_padding = 0
        self.title_horizontal_padding = 8
        self.title_vertical_padding = 10
