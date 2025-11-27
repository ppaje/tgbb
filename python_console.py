import sys
import io
import signal
import time
import resource
from contextlib import redirect_stdout, redirect_stderr
from security import SecurityManager

class TimeoutException(Exception):
    """Исключение для таймаута выполнения"""
    pass

class MemoryLimitException(Exception):
    """Исключение для превышения лимита памяти"""
    pass

class PythonConsole:
    def __init__(self):
        self.security = SecurityManager()
        self.local_vars = self.security.create_safe_globals()
        self.max_execution_time = 5  # секунд
        self.max_output_length = 2000
        self.max_memory_mb = 50  # MB
        self.execution_count = 0
        
        # Устанавливаем лимит памяти
        self._set_memory_limit()
        
    def _set_memory_limit(self):
        """Установка лимита памяти"""
        try:
            # Конвертируем MB в bytes
            memory_limit = self.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
        except (ValueError, resource.error) as e:
            # На некоторых системах могут быть ограничения
            print(f"⚠️ Не удалось установить лимит памяти: {e}")

    def reset_console(self):
        """Сброс состояния консоли"""
        self.local_vars = self.security.create_safe_globals()
        self.execution_count = 0
        return "🔄 Консоль сброшена! Все переменные очищены."

    def execute(self, code: str) -> str:
        """Безопасное выполнение Python кода"""
        if not code.strip():
            return "Введите код для выполнения"
        
        # Увеличиваем счетчик выполненных операций
        self.execution_count += 1
        
        # Проверка безопасности
        security_check = self.security.sanitize_input(code)
        if not security_check["is_safe"]:
            issues = security_check["issues"][:3]  # Показываем первые 3 ошибки
            return "❌ **Обнаружены проблемы с безопасностью:**\n" + "\n".join(issues)
        
        # Проверка длины кода
        if len(code) > 1000:
            return "❌ Код слишком длинный (максимум 1000 символов)"

        try:
            return self._execute_safely(code)
            
        except TimeoutException as e:
            return f"⏰ {str(e)}"
        except MemoryLimitException as e:
            return f"💥 {str(e)}"
        except Exception as e:
            return f"❌ Ошибка выполнения: {str(e)}"

    def _execute_safely(self, code: str) -> str:
        """Безопасное выполнение кода с ограничениями"""
        stdout = io.StringIO()
        stderr = io.StringIO()
        
        result = None
        
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                # Ограничение по времени выполнения
                result = self._execute_with_timeout(code)
                
            # Получаем вывод
            output = stdout.getvalue()
            error_output = stderr.getvalue()
            
            return self._format_result(code, output, error_output, result)
            
        except TimeoutException:
            raise
        except MemoryError:
            raise MemoryLimitException("Превышено потребление памяти")
        except Exception as e:
            # Перехватываем все остальные исключения
            return f"❌ Ошибка выполнения: {str(e)}"

    def _execute_with_timeout(self, code: str):
        """Выполнение кода с таймаутом"""
        
        def timeout_handler(signum, frame):
            raise TimeoutException(f"Время выполнения истекло ({self.max_execution_time} секунд)")
        
        # Устанавливаем обработчик таймаута (только для Unix-систем)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.max_execution_time)
            
            try:
                # Пробуем выполнить как выражение (для одной строки)
                return eval(code, self.local_vars)
            except SyntaxError:
                # Если не выражение, выполняем как statement
                exec(code, self.local_vars)
                return None
            except:
                # Если eval упал с другой ошибкой, пробуем exec
                exec(code, self.local_vars)
                return None
                
        finally:
            # Всегда отключаем таймер
            signal.alarm(0)

    def _format_result(self, code: str, output: str, error_output: str, result) -> str:
        """Форматирование результата выполнения"""
        response_parts = []
        
        # Добавляем стандартный вывод
        if output:
            response_parts.append(self._truncate_output(output))
        
        # Добавляем ошибки
        if error_output:
            # Фильтруем безопасные ошибки
            safe_error = self._filter_safe_errors(error_output)
            response_parts.append(f"Ошибка: {safe_error}")
        
        # Добавляем результат выражения
        if result is not None:
            response_parts.append(str(result))
        
        # Собираем финальный ответ
        response = '\n'.join(response_parts)
        
        if not response:
            response = "✅ Код выполнен успешно"
        
        return response.strip()

    def _truncate_output(self, output: str) -> str:
        """Обрезка слишком длинного вывода"""
        if len(output) > self.max_output_length:
            truncated = output[:self.max_output_length]
            # Сохраняем последнюю строку если она обрезана
            if '\n' in truncated:
                lines = truncated.split('\n')
                if len(lines) > 1:
                    truncated = '\n'.join(lines[:-1]) + "\n... (вывод обрезан)"
            else:
                truncated += "... (вывод обрезан)"
            return truncated
        return output

    def _filter_safe_errors(self, error_output: str) -> str:
        """Фильтрация ошибок для безопасного отображения"""
        # Убираем потенциально опасную информацию из traceback
        lines = error_output.split('\n')
        safe_lines = []
        
        for line in lines:
            # Оставляем только информативные части ошибок
            if any(keyword in line for keyword in [
                'Error:', 'Exception:', 'SyntaxError', 'NameError', 
                'TypeError', 'ValueError', 'IndexError', 'KeyError'
            ]):
                safe_lines.append(line)
            elif line.strip().startswith('File'):
                # Пропускаем информацию о файлах
                continue
                
        return '\n'.join(safe_lines) if safe_lines else "Произошла ошибка выполнения"

    def execute_multiline(self, code: str) -> str:
        """Выполнение многострочного кода с проверками"""
        # Для многострочного кода используем ту же систему безопасности
        return self.execute(code)

    def get_console_info(self) -> dict:
        """Получение информации о состоянии консоли"""
        return {
            "execution_count": self.execution_count,
            "variables_count": len([k for k in self.local_vars.keys() if not k.startswith('_')]),
            "memory_limit_mb": self.max_memory_mb,
            "timeout_seconds": self.max_execution_time
        }

    def get_available_variables(self) -> list:
        """Получение списка пользовательских переменных"""
        user_vars = []
        for key, value in self.local_vars.items():
            if not key.startswith('_') and key not in ['print', 'math']:
                try:
                    value_type = type(value).__name__
                    user_vars.append(f"{key} ({value_type})")
                except:
                    user_vars.append(f"{key} (unknown)")
        return user_vars

# Альтернативная реализация для Windows (где нет signal.SIGALRM)
class WindowsPythonConsole(PythonConsole):
    def _execute_with_timeout(self, code: str):
        """Реализация таймаута для Windows"""
        import threading
        
        class ExecutionThread(threading.Thread):
            def __init__(self, code, local_vars):
                threading.Thread.__init__(self)
                self.code = code
                self.local_vars = local_vars
                self.result = None
                self.exception = None
                
            def run(self):
                try:
                    try:
                        self.result = eval(self.code, self.local_vars)
                    except SyntaxError:
                        exec(self.code, self.local_vars)
                        self.result = None
                    except:
                        exec(self.code, self.local_vars)
                        self.result = None
                except Exception as e:
                    self.exception = e
        
        # Запускаем выполнение в отдельном потоке
        thread = ExecutionThread(code, self.local_vars)
        thread.start()
        thread.join(self.max_execution_time)
        
        if thread.is_alive():
            # Если поток еще жив, значит время истекло
            raise TimeoutException(f"Время выполнения истекло ({self.max_execution_time} секунд)")
        
        if thread.exception:
            raise thread.exception
            
        return thread.result

# Автоматически выбираем подходящую реализацию
import platform
if platform.system() == "Windows":
    PythonConsole = WindowsPythonConsole
