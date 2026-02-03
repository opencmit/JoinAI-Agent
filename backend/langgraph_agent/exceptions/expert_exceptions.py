"""
专家智能体异常定义模块
"""

import time
from typing import Dict, Any, Optional


class ExpertServiceException(Exception):
    """专家服务异常基类"""
    
    def __init__(
        self, 
        message: str, 
        agent_type: Optional[str] = None, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.agent_type = agent_type
        self.error_code = error_code or "EXPERT_SERVICE_ERROR"
        self.details = details or {}
        self.timestamp = time.time()
    
    def __str__(self) -> str:
        if self.agent_type:
            return f"[{self.agent_type}] {super().__str__()}"
        return super().__str__()
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}("
                f"message='{str(self)}', "
                f"agent_type='{self.agent_type}', "
                f"error_code='{self.error_code}')")
    
    def to_dict(self) -> Dict[str, Any]:
        """将异常信息转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "agent_type": self.agent_type,
            "error_code": self.error_code,
            "details": self.details,
            "timestamp": self.timestamp
        }


class ExpertServiceTimeoutException(ExpertServiceException):
    """专家服务超时异常"""
    
    def __init__(
        self, 
        message: str, 
        agent_type: Optional[str] = None,
        timeout_duration: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message, 
            agent_type=agent_type, 
            error_code="EXPERT_SERVICE_TIMEOUT",
            **kwargs
        )
        self.timeout_duration = timeout_duration
        self.operation = operation or "unknown"
        
        # 添加超时相关信息到details
        if timeout_duration:
            self.details["timeout_duration"] = timeout_duration
        self.details["operation"] = self.operation
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.timeout_duration:
            return f"{base_msg} (超时时间: {self.timeout_duration}s, 操作: {self.operation})"
        return f"{base_msg} (操作: {self.operation})"


class ExpertServiceUnavailableException(ExpertServiceException):
    """专家服务不可用异常"""
    
    def __init__(
        self, 
        message: str, 
        agent_type: Optional[str] = None,
        service_url: Optional[str] = None,
        reason: Optional[str] = None,
        retry_count: int = 0,
        **kwargs
    ):
        super().__init__(
            message, 
            agent_type=agent_type, 
            error_code="EXPERT_SERVICE_UNAVAILABLE",
            **kwargs
        )
        self.service_url = service_url
        self.reason = reason or "unknown"
        self.retry_count = retry_count
        
        # 添加服务相关信息到details
        if service_url:
            self.details["service_url"] = service_url
        self.details["reason"] = self.reason
        self.details["retry_count"] = retry_count
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.service_url:
            return f"{base_msg} (服务: {self.service_url}, 原因: {self.reason})"
        return f"{base_msg} (原因: {self.reason})"