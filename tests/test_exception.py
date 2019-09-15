import sys
import os
sys.path.insert(0, os.environ['CHAOS_LAYER_IMPORT_PATH'])

from chaos_lib import corrupt_exception
import unittest
import warnings
import boto3

client = boto3.client('ssm', region_name='eu-north-1')

os.environ['FAILURE_INJECTION_PARAM'] = 'test.config'


def ignore_warnings(test_func):
    def do_test(self, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            warnings.simplefilter("ignore", DeprecationWarning)
            test_func(self, *args, **kwargs)
    return do_test


@corrupt_exception
def handler_with_exception(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }


@corrupt_exception(exception_type=ValueError)
def handler_with_exception_arg(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }


@corrupt_exception(exception_type=TypeError, exception_msg='foobar')
def handler_with_exception_arg_2(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }


class TestExceptionMethods(unittest.TestCase):

    @ignore_warnings
    def setUp(self):
        os.environ['FAILURE_INJECTION_PARAM'] = 'test.config'
        client.put_parameter(
            Value="{ \"delay\": 400, \"isEnabled\": true, \"error_code\": 404, \"exception_msg\": \"I FAILED\", \"rate\": 1 }",
            Name='test.config',
            Type='String',
            Overwrite=True
        )

    @ignore_warnings
    def tearDown(self):
        client.delete_parameters(Names=['test.config'])

    @ignore_warnings
    def test_get_exception(self):
        with self.assertRaises(Exception):
            handler_with_exception('foo', 'bar')

    @ignore_warnings
    def test_get_exception_arg(self):
        with self.assertRaises(ValueError):
            handler_with_exception_arg('foo', 'bar')

    @ignore_warnings
    def handler_with_exception_arg_2(self):
        with self.assertRaises(TypeError):
            handler_with_exception_arg_2('foo', 'bar')


class TestExceptionMethodslowrate(unittest.TestCase):

    @ignore_warnings
    def setUp(self):
        os.environ['FAILURE_INJECTION_PARAM'] = 'test.config'
        client.put_parameter(
            Value="{ \"delay\": 400, \"isEnabled\": true, \"error_code\": 404, \"exception_msg\": \"I FAILED\", \"rate\": 0.0000001 }",
            Name='test.config',
            Type='String',
            Overwrite=True
        )

    @ignore_warnings
    def tearDown(self):
        client.delete_parameters(Names=['test.config'])

    @ignore_warnings
    def test_get_statuscode(self):
        handler_with_exception('foo', 'bar')
        self.assert_(True)


class TestExceptionMethodsnotenabled(unittest.TestCase):

    @ignore_warnings
    def setUp(self):
        os.environ['FAILURE_INJECTION_PARAM'] = 'test.config'
        client.put_parameter(
            Value="{ \"delay\": 400, \"isEnabled\": false, \"error_code\": 404, \"exception_msg\": \"I FAILED\", \"rate\": 1 }",
            Name='test.config',
            Type='String',
            Overwrite=True
        )

    @ignore_warnings
    def tearDown(self):
        client.delete_parameters(Names=['test.config'])

    @ignore_warnings
    def test_get_statuscode(self):
        handler_with_exception('foo', 'bar')
        self.assert_(True)


if __name__ == '__main__':
    unittest.main()
