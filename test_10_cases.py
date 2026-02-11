"""
Test 10 use cases with 5+ step flows for both versions
"""
import sys
import os

def test_compact_version():
    print('='*70)
    print('TESTING 10 USE CASES WITH 5+ STEP FLOWS - COMPACT VERSION')
    print('='*70)

    sys.path.insert(0, 'compact')
    from sagemaker_agent import CONFIG, BedrockClient, Agent, Response, ToolCall, TOOLS

    CONFIG.mock_mode = True

    class MultiStepTestClient(BedrockClient):
        def __init__(self):
            super().__init__(CONFIG.model_id, CONFIG.region, mock_mode=True)
            self.test_case = None
            self.step = 0

        def reset(self):
            self.step = 0

        def _mock_response(self, messages, tools):
            self.step += 1

            # Test 1: Explore codebase (5 steps)
            if self.test_case == 1:
                steps = [
                    ('Listing directory', [ToolCall('t1', 'list_dir', {'path': '.'})]),
                    ('Finding Python files', [ToolCall('t2', 'glob', {'pattern': '**/*.py'})]),
                    ('Reading README', [ToolCall('t3', 'read_file', {'file_path': 'README.md'})]),
                    ('Searching for main', [ToolCall('t4', 'grep', {'pattern': 'def main', 'limit': 3})]),
                    ('Checking structure', [ToolCall('t5', 'list_dir', {'path': 'compact'})]),
                ]

            # Test 2: Code analysis (5 steps)
            elif self.test_case == 2:
                steps = [
                    ('Finding code files', [ToolCall('t1', 'glob', {'pattern': '**/*.py'})]),
                    ('Searching classes', [ToolCall('t2', 'grep', {'pattern': 'class ', 'limit': 5})]),
                    ('Searching functions', [ToolCall('t3', 'grep', {'pattern': 'def ', 'limit': 5})]),
                    ('Reading main file', [ToolCall('t4', 'read_file', {'file_path': 'compact/sagemaker_agent.py', 'limit': 50})]),
                    ('Checking imports', [ToolCall('t5', 'grep', {'pattern': '^import|^from', 'limit': 10})]),
                ]

            # Test 3: Project setup (5 steps)
            elif self.test_case == 3:
                steps = [
                    ('Checking directory', [ToolCall('t1', 'list_dir', {'path': '.'})]),
                    ('Creating task list', [ToolCall('t2', 'todo_write', {'todos': [
                        {'content': 'Check requirements', 'status': 'in_progress', 'activeForm': 'Checking'},
                        {'content': 'Read docs', 'status': 'pending', 'activeForm': 'Reading'},
                        {'content': 'Run tests', 'status': 'pending', 'activeForm': 'Testing'},
                    ]})]),
                    ('Reading requirements', [ToolCall('t3', 'read_file', {'file_path': 'compact/requirements.txt'})]),
                    ('Updating tasks', [ToolCall('t4', 'todo_write', {'todos': [
                        {'content': 'Check requirements', 'status': 'completed', 'activeForm': 'Done'},
                        {'content': 'Read docs', 'status': 'in_progress', 'activeForm': 'Reading'},
                    ]})]),
                    ('Reading guide', [ToolCall('t5', 'read_file', {'file_path': 'compact/GUIDE.md', 'limit': 30})]),
                ]

            # Test 4: Search and analyze (5 steps)
            elif self.test_case == 4:
                steps = [
                    ('Finding all tools', [ToolCall('t1', 'grep', {'pattern': 'def tool_', 'limit': 20})]),
                    ('Finding security code', [ToolCall('t2', 'grep', {'pattern': 'Security', 'case_insensitive': True})]),
                    ('Reading security', [ToolCall('t3', 'read_file', {'file_path': 'complete/core/security.py', 'limit': 50})]),
                    ('Finding tests', [ToolCall('t4', 'glob', {'pattern': '**/*test*.py'})]),
                    ('Checking audit', [ToolCall('t5', 'grep', {'pattern': 'audit', 'case_insensitive': True})]),
                ]

            # Test 5: Bash operations (5 steps)
            elif self.test_case == 5:
                steps = [
                    ('Checking Python', [ToolCall('t1', 'bash', {'command': 'python --version'})]),
                    ('Listing files', [ToolCall('t2', 'bash', {'command': 'dir'})]),
                    ('Checking pip', [ToolCall('t3', 'bash', {'command': 'pip --version'})]),
                    ('Echo test', [ToolCall('t4', 'bash', {'command': 'echo Test passed'})]),
                    ('Current dir', [ToolCall('t5', 'bash', {'command': 'cd'})]),
                ]

            # Test 6: Python execution (5 steps)
            elif self.test_case == 6:
                steps = [
                    ('Simple calc', [ToolCall('t1', 'python_exec', {'code': 'print(2+2)'})]),
                    ('List comp', [ToolCall('t2', 'python_exec', {'code': 'print([x**2 for x in range(5)])'})]),
                    ('Dict ops', [ToolCall('t3', 'python_exec', {'code': 'd = {"a": 1}; print(d)'})]),
                    ('String ops', [ToolCall('t4', 'python_exec', {'code': 'print("hello".upper())'})]),
                    ('Import test', [ToolCall('t5', 'python_exec', {'code': 'import os; print(os.getcwd())'})]),
                ]

            # Test 7: Multi-file read (5 steps)
            elif self.test_case == 7:
                steps = [
                    ('Finding MDs', [ToolCall('t1', 'glob', {'pattern': '**/*.md'})]),
                    ('Reading README', [ToolCall('t2', 'read_file', {'file_path': 'README.md'})]),
                    ('Reading compact README', [ToolCall('t3', 'read_file', {'file_path': 'compact/README.md'})]),
                    ('Reading complete README', [ToolCall('t4', 'read_file', {'file_path': 'complete/README.md'})]),
                    ('Listing all', [ToolCall('t5', 'list_dir', {'path': '.'})]),
                ]

            # Test 8: Error handling (5 steps)
            elif self.test_case == 8:
                steps = [
                    ('Read nonexistent', [ToolCall('t1', 'read_file', {'file_path': 'nonexistent.txt'})]),
                    ('Invalid glob', [ToolCall('t2', 'glob', {'pattern': '**/*.xyz123'})]),
                    ('Bad image', [ToolCall('t3', 'view_image', {'file_path': 'fake.png'})]),
                    ('Valid list', [ToolCall('t4', 'list_dir', {'path': '.'})]),
                    ('Recovery grep', [ToolCall('t5', 'grep', {'pattern': 'def', 'limit': 2})]),
                ]

            # Test 9: Security tests (5 steps)
            elif self.test_case == 9:
                steps = [
                    ('Path traversal 1', [ToolCall('t1', 'read_file', {'file_path': '../../../etc/passwd'})]),
                    ('Path traversal 2', [ToolCall('t2', 'read_file', {'file_path': '..\\..\\windows\\system32'})]),
                    ('Dangerous cmd', [ToolCall('t3', 'bash', {'command': 'rm -rf /'})]),
                    ('Valid read', [ToolCall('t4', 'read_file', {'file_path': 'README.md'})]),
                    ('Valid bash', [ToolCall('t5', 'bash', {'command': 'echo safe'})]),
                ]

            # Test 10: Combined workflow (5 steps)
            elif self.test_case == 10:
                steps = [
                    ('Init tasks', [ToolCall('t1', 'todo_write', {'todos': [
                        {'content': 'Explore', 'status': 'in_progress', 'activeForm': 'Exploring'}
                    ]})]),
                    ('List + Glob', [
                        ToolCall('t2a', 'list_dir', {'path': '.'}),
                        ToolCall('t2b', 'glob', {'pattern': '*.md'})
                    ]),
                    ('Read + Grep', [
                        ToolCall('t3a', 'read_file', {'file_path': 'README.md'}),
                        ToolCall('t3b', 'grep', {'pattern': 'tool', 'limit': 3})
                    ]),
                    ('Python calc', [ToolCall('t4', 'python_exec', {'code': 'print(sum(range(10)))'})]),
                    ('Complete tasks', [ToolCall('t5', 'todo_write', {'todos': [
                        {'content': 'Explore', 'status': 'completed', 'activeForm': 'Done'}
                    ]})]),
                ]
            else:
                steps = []

            if self.step <= len(steps):
                text, calls = steps[self.step - 1]
                return Response(text, calls, 'tool_use', {'input_tokens': 100, 'output_tokens': 50})
            else:
                return Response('All steps completed.', [], 'end_turn', {'input_tokens': 50, 'output_tokens': 20})

    # Test cases
    test_cases = [
        (1, 'Explore codebase'),
        (2, 'Code analysis'),
        (3, 'Project setup with todos'),
        (4, 'Search and analyze'),
        (5, 'Bash operations'),
        (6, 'Python execution'),
        (7, 'Multi-file reading'),
        (8, 'Error handling'),
        (9, 'Security validation'),
        (10, 'Combined workflow'),
    ]

    client = MultiStepTestClient()
    all_results = []

    for case_num, description in test_cases:
        print(f'\n{"="*70}')
        print(f'Test {case_num}: {description}')
        print('='*70)

        client.test_case = case_num
        client.reset()

        tool_calls = []
        tool_results = []
        errors = []

        def capture(text):
            if '[Calling' in text:
                tool_name = text.split('[Calling ')[1].split('...]')[0] if '[Calling ' in text else text
                tool_calls.append(tool_name)
                print(f'  Step {len(tool_calls)}: [Calling {tool_name}...]')
            elif ' result]' in text:
                tool_results.append(text)
                preview = text[:80].replace('\n', ' ')
                print(f'         Result: {preview}...')
                if 'error' in text.lower() or 'blocked' in text.lower():
                    errors.append(text[:50])
            elif text.startswith('['):
                print(f'  Info: {text[:60]}')

        agent = Agent(client, f'test_{case_num}')

        try:
            result = agent.run(f'Run test case {case_num}', output_fn=capture)

            print(f'\n  Summary:')
            print(f'    Tool calls made: {len(tool_calls)}')
            print(f'    Tool results: {len(tool_results)}')
            print(f'    Errors/blocks: {len(errors)}')

            # Determine pass/fail
            if case_num == 9:  # Security test - expect blocks
                passed = len(errors) >= 3
                status = 'PASS' if passed else 'FAIL'
            elif case_num == 8:  # Error handling - expect some errors
                passed = len(errors) >= 2 and len(tool_calls) >= 5
                status = 'PASS' if passed else 'FAIL'
            else:
                passed = len(tool_calls) >= 5 and len(tool_results) >= 5
                status = 'PASS' if passed else 'FAIL'

            print(f'    STATUS: {status}')
            all_results.append((case_num, description, status, len(tool_calls)))

        except Exception as e:
            print(f'  ERROR: {e}')
            import traceback
            traceback.print_exc()
            all_results.append((case_num, description, 'ERROR', 0))

    print('\n' + '='*70)
    print('FINAL SUMMARY - COMPACT VERSION')
    print('='*70)
    passed = sum(1 for _, _, s, _ in all_results if s == 'PASS')
    for num, desc, status, steps in all_results:
        icon = '[OK]  ' if status == 'PASS' else '[FAIL]'
        print(f'  {icon} Test {num}: {desc} ({steps} steps)')
    print(f'\nTotal: {passed}/10 PASSED')

    return all_results


def test_complete_version():
    print('\n\n' + '='*70)
    print('TESTING 10 USE CASES WITH 5+ STEP FLOWS - COMPLETE VERSION')
    print('='*70)

    # Clear modules
    for mod in list(sys.modules.keys()):
        if mod.startswith('compact') or mod.startswith('sagemaker'):
            del sys.modules[mod]

    sys.path = [p for p in sys.path if 'compact' not in p]
    sys.path.insert(0, 'complete')

    from core.bedrock_client import BedrockClient, Response, ToolCall
    from core.tools import ToolRegistry, ToolContext
    from core.agent_loop import AgentLoop
    from tools import ALL_TOOLS

    class MultiStepTestClient(BedrockClient):
        def __init__(self):
            super().__init__('anthropic.claude-3-5-sonnet-20241022-v2:0', 'ap-southeast-2', mock_mode=True)
            self.test_case = None
            self.step = 0

        def reset(self):
            self.step = 0

        def _mock_response(self, messages, tools):
            self.step += 1

            # Same test cases as compact
            if self.test_case == 1:
                steps = [
                    ('Listing directory', [ToolCall('t1', 'list_dir', {'path': '.'})]),
                    ('Finding Python files', [ToolCall('t2', 'glob', {'pattern': '**/*.py'})]),
                    ('Reading README', [ToolCall('t3', 'read_file', {'file_path': 'README.md'})]),
                    ('Searching for main', [ToolCall('t4', 'grep', {'pattern': 'def main', 'limit': 3})]),
                    ('Checking structure', [ToolCall('t5', 'list_dir', {'path': 'compact'})]),
                ]
            elif self.test_case == 2:
                steps = [
                    ('Finding code files', [ToolCall('t1', 'glob', {'pattern': '**/*.py'})]),
                    ('Searching classes', [ToolCall('t2', 'grep', {'pattern': 'class ', 'limit': 5})]),
                    ('Searching functions', [ToolCall('t3', 'grep', {'pattern': 'def ', 'limit': 5})]),
                    ('Reading main file', [ToolCall('t4', 'read_file', {'file_path': 'compact/sagemaker_agent.py', 'limit': 50})]),
                    ('Checking imports', [ToolCall('t5', 'grep', {'pattern': '^import|^from', 'limit': 10})]),
                ]
            elif self.test_case == 3:
                steps = [
                    ('Checking directory', [ToolCall('t1', 'list_dir', {'path': '.'})]),
                    ('Creating tasks', [ToolCall('t2', 'todo_write', {'todos': [{'content': 'Task 1', 'status': 'pending', 'activeForm': 'Working'}]})]),
                    ('Reading file', [ToolCall('t3', 'read_file', {'file_path': 'compact/requirements.txt'})]),
                    ('Update tasks', [ToolCall('t4', 'todo_write', {'todos': [{'content': 'Task 1', 'status': 'completed', 'activeForm': 'Done'}]})]),
                    ('Final read', [ToolCall('t5', 'read_file', {'file_path': 'README.md'})]),
                ]
            elif self.test_case == 4:
                steps = [
                    ('Step 1', [ToolCall('t1', 'grep', {'pattern': 'def tool_', 'limit': 5})]),
                    ('Step 2', [ToolCall('t2', 'grep', {'pattern': 'Security'})]),
                    ('Step 3', [ToolCall('t3', 'read_file', {'file_path': 'complete/core/security.py', 'limit': 30})]),
                    ('Step 4', [ToolCall('t4', 'glob', {'pattern': '**/*.py'})]),
                    ('Step 5', [ToolCall('t5', 'grep', {'pattern': 'audit'})]),
                ]
            elif self.test_case == 5:
                steps = [
                    ('Bash 1', [ToolCall('t1', 'bash', {'command': 'python --version'})]),
                    ('Bash 2', [ToolCall('t2', 'bash', {'command': 'dir'})]),
                    ('Bash 3', [ToolCall('t3', 'bash', {'command': 'pip --version'})]),
                    ('Bash 4', [ToolCall('t4', 'bash', {'command': 'echo Test'})]),
                    ('Bash 5', [ToolCall('t5', 'bash', {'command': 'cd'})]),
                ]
            elif self.test_case == 6:
                steps = [
                    ('Py 1', [ToolCall('t1', 'python_exec', {'code': 'print(1+1)'})]),
                    ('Py 2', [ToolCall('t2', 'python_exec', {'code': 'print(2+2)'})]),
                    ('Py 3', [ToolCall('t3', 'python_exec', {'code': 'print(3+3)'})]),
                    ('Py 4', [ToolCall('t4', 'python_exec', {'code': 'print(4+4)'})]),
                    ('Py 5', [ToolCall('t5', 'python_exec', {'code': 'print(5+5)'})]),
                ]
            elif self.test_case == 7:
                steps = [
                    ('Read 1', [ToolCall('t1', 'glob', {'pattern': '**/*.md'})]),
                    ('Read 2', [ToolCall('t2', 'read_file', {'file_path': 'README.md'})]),
                    ('Read 3', [ToolCall('t3', 'read_file', {'file_path': 'compact/README.md'})]),
                    ('Read 4', [ToolCall('t4', 'read_file', {'file_path': 'complete/README.md'})]),
                    ('Read 5', [ToolCall('t5', 'list_dir', {'path': '.'})]),
                ]
            elif self.test_case == 8:
                steps = [
                    ('Err 1', [ToolCall('t1', 'read_file', {'file_path': 'nonexistent.txt'})]),
                    ('Err 2', [ToolCall('t2', 'glob', {'pattern': '**/*.xyz123'})]),
                    ('Err 3', [ToolCall('t3', 'view_image', {'file_path': 'fake.png'})]),
                    ('Ok 1', [ToolCall('t4', 'list_dir', {'path': '.'})]),
                    ('Ok 2', [ToolCall('t5', 'grep', {'pattern': 'def', 'limit': 2})]),
                ]
            elif self.test_case == 9:
                steps = [
                    ('Sec 1', [ToolCall('t1', 'read_file', {'file_path': '../../../etc/passwd'})]),
                    ('Sec 2', [ToolCall('t2', 'read_file', {'file_path': '..\\..\\windows'})]),
                    ('Sec 3', [ToolCall('t3', 'bash', {'command': 'rm -rf /'})]),
                    ('Ok 1', [ToolCall('t4', 'read_file', {'file_path': 'README.md'})]),
                    ('Ok 2', [ToolCall('t5', 'bash', {'command': 'echo safe'})]),
                ]
            elif self.test_case == 10:
                steps = [
                    ('Combo 1', [ToolCall('t1', 'todo_write', {'todos': [{'content': 'Test', 'status': 'pending', 'activeForm': 'Testing'}]})]),
                    ('Combo 2', [ToolCall('t2a', 'list_dir', {'path': '.'}), ToolCall('t2b', 'glob', {'pattern': '*.md'})]),
                    ('Combo 3', [ToolCall('t3a', 'read_file', {'file_path': 'README.md'}), ToolCall('t3b', 'grep', {'pattern': 'tool', 'limit': 3})]),
                    ('Combo 4', [ToolCall('t4', 'python_exec', {'code': 'print(42)'})]),
                    ('Combo 5', [ToolCall('t5', 'todo_write', {'todos': [{'content': 'Test', 'status': 'completed', 'activeForm': 'Done'}]})]),
                ]
            else:
                steps = []

            if self.step <= len(steps):
                text, calls = steps[self.step - 1]
                return Response(text, calls, 'tool_use', {'input_tokens': 100, 'output_tokens': 50})
            else:
                return Response('Done.', [], 'end_turn', {'input_tokens': 50, 'output_tokens': 20})

    test_cases = [
        (1, 'Explore codebase'),
        (2, 'Code analysis'),
        (3, 'Project setup with todos'),
        (4, 'Search and analyze'),
        (5, 'Bash operations'),
        (6, 'Python execution'),
        (7, 'Multi-file reading'),
        (8, 'Error handling'),
        (9, 'Security validation'),
        (10, 'Combined workflow'),
    ]

    client = MultiStepTestClient()
    registry = ToolRegistry()
    for tool in ALL_TOOLS:
        registry.register(tool)

    all_results = []

    for case_num, description in test_cases:
        print(f'\n{"="*70}')
        print(f'Test {case_num}: {description}')
        print('='*70)

        client.test_case = case_num
        client.reset()

        ctx = ToolContext(working_dir=os.getcwd(), session_id=f'test_{case_num}')

        tool_calls = []
        tool_results = []
        errors = []

        def on_text(t):
            pass

        def on_tool_call(name, inp):
            tool_calls.append(name)
            print(f'  Step {len(tool_calls)}: [Calling {name}...]')

        def on_tool_result(name, result):
            tool_results.append(result)
            preview = result[:80].replace('\n', ' ')
            print(f'         Result: {preview}...')
            if 'error' in result.lower() or 'blocked' in result.lower():
                errors.append(result[:50])

        agent = AgentLoop(
            client=client,
            registry=registry,
            system_prompt='Test',
            context=ctx,
            on_text=on_text,
            on_tool_call=on_tool_call,
            on_tool_result=on_tool_result,
        )

        try:
            result = agent.run(f'Run test case {case_num}')

            print(f'\n  Summary:')
            print(f'    Tool calls made: {len(tool_calls)}')
            print(f'    Tool results: {len(tool_results)}')
            print(f'    Errors/blocks: {len(errors)}')

            if case_num == 9:
                passed = len(errors) >= 3
                status = 'PASS' if passed else 'FAIL'
            elif case_num == 8:
                passed = len(errors) >= 2 and len(tool_calls) >= 5
                status = 'PASS' if passed else 'FAIL'
            else:
                passed = len(tool_calls) >= 5 and len(tool_results) >= 5
                status = 'PASS' if passed else 'FAIL'

            print(f'    STATUS: {status}')
            all_results.append((case_num, description, status, len(tool_calls)))

        except Exception as e:
            print(f'  ERROR: {e}')
            import traceback
            traceback.print_exc()
            all_results.append((case_num, description, 'ERROR', 0))

    print('\n' + '='*70)
    print('FINAL SUMMARY - COMPLETE VERSION')
    print('='*70)
    passed = sum(1 for _, _, s, _ in all_results if s == 'PASS')
    for num, desc, status, steps in all_results:
        icon = '[OK]  ' if status == 'PASS' else '[FAIL]'
        print(f'  {icon} Test {num}: {desc} ({steps} steps)')
    print(f'\nTotal: {passed}/10 PASSED')

    return all_results


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    compact_results = test_compact_version()
    complete_results = test_complete_version()

    print('\n\n' + '='*70)
    print('FINAL COMPARISON')
    print('='*70)

    compact_pass = sum(1 for _, _, s, _ in compact_results if s == 'PASS')
    complete_pass = sum(1 for _, _, s, _ in complete_results if s == 'PASS')

    print(f'\nCompact Version:  {compact_pass}/10 PASSED')
    print(f'Complete Version: {complete_pass}/10 PASSED')

    if compact_pass == 10 and complete_pass == 10:
        print('\n*** BOTH VERSIONS PASS ALL 10 USE CASES ***')
    else:
        print('\n*** SOME TESTS FAILED - REVIEW ABOVE ***')
