import re
import ast

class SecurityManager:
    """Менеджер безопасности для бота"""
    
    def __init__(self):
        # Белый список встроенных функций
        self.whitelisted_builtins = {
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
            'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict', 
            'dir', 'divmod', 'enumerate', 'filter', 'float', 'format', 'frozenset',
            'getattr', 'globals', 'hasattr', 'hash', 'hex', 'id', 'input', 'int',
            'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals', 'map',
            'max', 'min', 'next', 'object', 'oct', 'ord', 'pow', 'print', 'range',
            'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted',
            'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'
        }
        
        # Черный список опасных модулей
        self.dangerous_modules = {
            'os', 'sys', 'subprocess', 'socket', 'urllib', 'requests',
            '__import__', 'eval', 'exec', 'compile', 'open', 'file',
            'input', 'raw_input', '__builtins__'
        }
        
        # Черный список опасных функций и атрибутов
        self.dangerous_patterns = [
            r'__import__',
            r'eval\s*\(',
            r'exec\s*\(',
            r'compile\s*\(',
            r'open\s*\(',
            r'file\s*\(',
            r'input\s*\(',
            r'__.*__',
            r'\.\_.*',
            r'import\s+(os|sys|subprocess|socket|urllib|requests)',
            r'from\s+(os|sys|subprocess|socket|urllib|requests)',
        ]
    
    def sanitize_input(self, code: str) -> dict:
        """Проверка безопасности кода"""
        issues = []
        is_safe = True
        
        # Проверка на опасные функции
        for pattern in self.dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(f"❌ Обнаружено опасное выражение: {pattern}")
                is_safe = False
        
        # Проверка на опасные модули
        for module in self.dangerous_modules:
            if re.search(rf'\b{module}\b', code, re.IGNORECASE):
                if module not in ['eval', 'exec', 'compile']:  # Уже проверены выше
                    issues.append(f"❌ Модуль '{module}' запрещен")
                    is_safe = False
        
        # Проверка синтаксиса
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(f"❌ Синтаксическая ошибка: {str(e)}")
            is_safe = False
        
        return {
            "is_safe": is_safe,
            "issues": issues
        }
    
    def create_safe_globals(self):
        """Создание безопасного глобального контекста"""
        safe_globals = {}
        
        # Базовые встроенные функции
        safe_builtins = {}
        for func in self.whitelisted_builtins:
            if hasattr(__builtins__, func) if isinstance(__builtins__, dict) else hasattr(__builtins__, func):
                try:
                    if isinstance(__builtins__, dict):
                        safe_builtins[func] = __builtins__[func]
                    else:
                        safe_builtins[func] = getattr(__builtins__, func)
                except:
                    pass
        
        safe_globals['__builtins__'] = safe_builtins
        
        # Математические функции
        try:
            import math
            safe_math = {
                'sqrt', 'pow', 'sin', 'cos', 'tan', 'log', 'log10', 
                'pi', 'e', 'ceil', 'floor', 'fabs', 'factorial',
                'degrees', 'radians', 'acos', 'asin', 'atan'
            }
            
            safe_globals['math'] = {
                func: getattr(math, func) 
                for func in safe_math 
                if hasattr(math, func)
            }
        except ImportError:
            pass
        
        # JSON для работы с данными
        try:
            import json
            safe_globals['json'] = json
        except ImportError:
            pass
        
        # datetime для работы со временем
        try:
            import datetime
            safe_globals['datetime'] = datetime
        except ImportError:
            pass
        
        # random для случайных чисел
        try:
            import random
            safe_globals['random'] = random
        except ImportError:
            pass
        
        return safe_globals
    
    def check_memory_usage(self) -> dict:
        """Проверка использования памяти"""
        import psutil
        import os
        
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            return {
                "memory_mb": round(memory_mb, 2),
                "healthy": memory_mb < 500
            }
        except:
            return {
                "memory_mb": 0,
                "healthy": True
            }
