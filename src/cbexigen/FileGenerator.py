# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

from pathlib import Path
import cbexigen.tools_config as tools_conf
from cbexigen import SchemaAnalyzer as Analyzer
from cbexigen.typeDefinitions import AnalyzerData
from cbexigen import tools_generator, tools, tools_logging
from cbexigen.datatype_classes import DatatypeHeader, DatatypeCode
from cbexigen.decoder_classes import ExiDecoderHeader, ExiDecoderCode
from cbexigen.encoder_classes import ExiEncoderHeader, ExiEncoderCode


class FileGenerator(object):

    def __init__(self):
        self.__analyzer_data = AnalyzerData()
        self.__schema = None

        self.__analyzer_data_printed = False
        self.__analyzer_data.add_debug_code_enabled = tools_conf.CONFIG_PARAMS['add_debug_code']
        self.__analyzer_data.debug_code_current_message_id = 1

    def __analyzer_data_clear(self):
        self.__analyzer_data.schema_identifier = ''
        self.__analyzer_data.root_elements.clear()
        self.__analyzer_data.generate_elements.clear()
        self.__analyzer_data.generate_elements_types.clear()

        self.__analyzer_data.known_elements.clear()
        self.__analyzer_data.known_particles.clear()
        self.__analyzer_data.known_prototypes.clear()
        self.__analyzer_data.known_enums.clear()

        self.__analyzer_data.max_occurs_changed.clear()
        self.__analyzer_data.namespace_elements.clear()
        self.__analyzer_data.schema_builtin_types.clear()

        self.__analyzer_data.debug_code_current_message_id = 1
        self.__analyzer_data.debug_code_messages.clear()

    def __init_schema(self, parameters):
        schema_full_name = Path(tools_conf.CONFIG_ARGS['schema_base_dir'], parameters['schema']).resolve()
        schema_path = schema_full_name.parent.resolve()
        schema_prefix = parameters['prefix']

        if self.__schema is not None:
            schema_file = self.__schema.get_current_schema_file().name
            schema_url = self.__schema.get_current_schema().base_url
            if str(schema_full_name) != schema_file or str(schema_path) != schema_url:
                self.__schema.close()
                self.__schema = None
                self.__analyzer_data_clear()
                self.__analyzer_data_printed = False
            else:
                tools_logging.msg_write('*** Generator info: Schema did not change. Using same analyzer data. ***', True)

        if self.__schema is None:
            tools_logging.msg_write('*** Generator info: Schema changed. Generating new analyzer data. ***', True)
            self.__schema = Analyzer.SchemaAnalyzer(schema_full_name, schema_path, self.__analyzer_data,
                                                    schema_prefix)
            self.__schema.open()

            tools_logging.msg_write('*** Elements: ' + parameters['schema'] + ' ***', True)
            self.__schema.analyze_schema_elements()

    def __generate_debug_files(self, parameters):
        if not self.__analyzer_data.add_debug_code_enabled or parameters['type'] == 'converter':
            return

        if parameters['type'] == 'static' or parameters['type'] == 'converter':
            return

        config_h = parameters.get('h', None)
        config_c = parameters.get('c', None)
        if config_h is None or config_c is None:
            tools_logging.log_write_error(f'Caution! No h- or c-parameters passed. '
                                          f'{self.__class__.__name__}.{self.__generate_debug_files.__name__}')
            return

        generator = tools_generator.get_generator()
        log_name_h = 'debug_' + config_h['filename']
        log_name_c = 'debug_' + config_c['filename']
        callback_prefix = f'{parameters["prefix"]}{parameters["type"]}_'
        status_log_name = f"status_log_{parameters['prefix']}{parameters['type']}.txt"
        file_key = f"{parameters['type']}_{str(parameters['prefix']).upper()}DEBUG_LOG_H"

        temp = generator.get_template('static_code/exi_debug_log.h.jinja')
        code = temp.render(filename=log_name_h, filekey=file_key,
                           general_defines=self.__analyzer_data.debug_code_messages,
                           callback_prefix=callback_prefix)
        tools.save_code_to_file(log_name_h, code, parameters['folder'])

        temp = generator.get_template('static_code/exi_debug_log.c.jinja')
        code = temp.render(include_name=log_name_h, status_log_name=status_log_name,
                           general_defines=self.__analyzer_data.debug_code_messages,
                           callback_prefix=callback_prefix)
        tools.save_code_to_file(log_name_c, code, parameters['folder'])

        self.__analyzer_data.debug_code_current_message_id = 1
        self.__analyzer_data.debug_code_messages.clear()

    def __generate_static_h(self, parameters):
        config = parameters.get('h', None)
        if config is None:
            tools_logging.log_write_error(f'Caution! No h-parameters passed. '
                                          f'{self.__class__.__name__}.{self.__generate_static_h.__name__}')
            return

        try:
            generator = tools_generator.get_generator()
            temp = generator.get_template(config['template'])
            code = temp.render(filename=config['filename'], filekey=config['identifier'],
                               add_debug_code=self.__analyzer_data.add_debug_code_enabled)

            tools.save_code_to_file(config['filename'], code, parameters['folder'])
        except KeyError as err:
            tools_logging.log_write_error(f'Exception in {self.__class__.__name__}.{self.__generate_static_h.__name__} '
                                          f'(KeyError): {err}')

    def __generate_static_c(self, parameters):
        config = parameters.get('c', None)
        if config is None:
            tools_logging.log_write_error(f'Caution! No c-parameters passed. '
                                          f'{self.__class__.__name__}.{self.__generate_static_c.__name__}')
            return

        try:
            generator = tools_generator.get_generator()
            temp = generator.get_template(config['template'])
            code = temp.render(filename=config['filename'], filekey=config['identifier'],
                               add_debug_code=self.__analyzer_data.add_debug_code_enabled)

            tools.save_code_to_file(config['filename'], code, parameters['folder'])
        except KeyError as err:
            tools_logging.log_write_error(f'Exception in {self.__class__.__name__}.{self.__generate_static_c.__name__} '
                                          f'(KeyError): {err}')

    @staticmethod
    def __generate_converter_h(current_schema, parameters, info_data: AnalyzerData):
        header = DatatypeHeader(current_schema, parameters, info_data, True)
        header.generate_file()

    @staticmethod
    def __generate_converter_c(current_schema, parameters, info_data: AnalyzerData):
        code = DatatypeCode(current_schema, parameters, info_data, True)
        code.generate_file()
        code.disable_logging()

    @staticmethod
    def __generate_decoder_h(parameters, info_data: AnalyzerData):
        header = ExiDecoderHeader(parameters, True)
        header.generate_file()

    @staticmethod
    def __generate_decoder_c(parameters, info_data: AnalyzerData):
        code = ExiDecoderCode(parameters, info_data, True)
        code.generate_file()
        code.disable_logging()

    @staticmethod
    def __generate_encoder_h(parameters, info_data: AnalyzerData):
        header = ExiEncoderHeader(parameters, True)
        header.generate_file()

    @staticmethod
    def __generate_encoder_c(parameters, info_data: AnalyzerData):
        code = ExiEncoderCode(parameters, info_data, True)
        code.generate_file()
        code.disable_logging()

    def __generate(self, is_header, parameters):
        func_type = parameters['type']

        if func_type == 'static':
            if is_header:
                self.__generate_static_h(parameters)
            else:
                self.__generate_static_c(parameters)
        elif func_type == 'converter':
            self.__init_schema(parameters)

            # call file generation
            current_schema = self.__schema.get_current_schema()
            tools_logging.msg_write('*** Generator info: ' + parameters['schema'] + ' ***', True)

            if is_header:
                self.__generate_converter_h(current_schema, parameters, self.__analyzer_data)
            else:
                self.__generate_converter_c(current_schema, parameters, self.__analyzer_data)

            if not self.__analyzer_data_printed:
                self.__schema.write_analyzer_data_to_log()
                self.__analyzer_data_printed = True
        elif func_type == 'decoder':
            self.__init_schema(parameters)

            # call file generation
            tools_logging.msg_write('*** Generator info: ' + parameters['schema'] + ' ***', True)

            if is_header:
                self.__generate_decoder_h(parameters, self.__analyzer_data)
            else:
                self.__generate_decoder_c(parameters, self.__analyzer_data)

            if not self.__analyzer_data_printed:
                self.__schema.write_analyzer_data_to_log()
                self.__analyzer_data_printed = True
        elif func_type == 'encoder':
            self.__init_schema(parameters)

            # call file generation
            tools_logging.msg_write('*** Generator info: ' + parameters['schema'] + ' ***', True)

            if is_header:
                self.__generate_encoder_h(parameters, self.__analyzer_data)
            else:
                self.__generate_encoder_c(parameters, self.__analyzer_data)

            if not self.__analyzer_data_printed:
                self.__schema.write_analyzer_data_to_log()
                self.__analyzer_data_printed = True
        else:
            tools_logging.msg_write('exec_function: type unknown ' + func_type)

    def generate_files(self):
        config_module = tools_conf.get_config_module()
        files = config_module.c_files_to_generate

        self.__schema = None
        self.__analyzer_data_clear()

        for name, params in files.items():
            h_config = params.get('h', None)
            if h_config is not None:
                # h-file has to be generated
                tools_logging.msg_write('GENERATING: ' + h_config['filename'], True)
                self.__generate(True, params)

            c_config = params.get('c', None)
            if c_config is not None:
                if self.__analyzer_data.add_debug_code_enabled:
                    if params['prefix'] != '' and params['type'] != 'converter' and params['type'] != 'static':
                        log_name = 'debug_' + str(c_config['filename'])[:len(c_config['filename']) - 1] + 'h'
                        params['c']['include_other'].append(log_name)
                # c-file has to be generated
                tools_logging.msg_write('GENERATING: ' + c_config['filename'], True)
                self.__generate(False, params)

                self.__generate_debug_files(params)
