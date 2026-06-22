/**
 * 工具函数模块
 * 提供各种通用工具函数
 */

/**
 * 格式化日期时间
 * @param {Date|string|number} date - 日期对象或时间戳或日期字符串
 * @param {string} format - 格式化模板，默认为 'YYYY-MM-DD HH:mm:ss'
 * @returns {string} 格式化后的日期字符串
 */
export function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
  // 如果是字符串或数字，转换为Date对象
  if (!(date instanceof Date)) {
    date = new Date(date);
  }

  // 检查日期是否有效
  if (isNaN(date.getTime())) {
    return '';
  }

  // 年份处理
  const year = date.getFullYear();
  // 月份处理（从0开始，需要+1，并补零）
  const month = String(date.getMonth() + 1).padStart(2, '0');
  // 日期处理（补零）
  const day = String(date.getDate()).padStart(2, '0');
  // 小时处理（补零）
  const hours = String(date.getHours()).padStart(2, '0');
  // 分钟处理（补零）
  const minutes = String(date.getMinutes()).padStart(2, '0');
  // 秒数处理（补零）
  const seconds = String(date.getSeconds()).padStart(2, '0');

  // 根据格式化模板替换相应部分
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds);
}

/**
 * 格式化日期（不含时间）
 * @param {Date|string|number} date - 日期对象或时间戳或日期字符串
 * @returns {string} 格式化后的日期字符串 YYYY-MM-DD
 */
export function formatDate(date) {
  return formatDateTime(date, 'YYYY-MM-DD');
}

/**
 * 格式化时间（不含日期）
 * @param {Date|string|number} date - 日期对象或时间戳或日期字符串
 * @returns {string} 格式化后的时间字符串 HH:mm:ss
 */
export function formatTime(date) {
  return formatDateTime(date, 'HH:mm:ss');
}

/**
 * 格式化时长（秒转换为时分秒）
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的时长字符串 HH:mm:ss
 */
export function formatDuration(seconds) {
  if (typeof seconds !== 'number' || isNaN(seconds) || seconds < 0) {
    return '00:00:00';
  }

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

/**
 * 深拷贝（JSON方式，简单实现）
 * @param {any} obj - 要拷贝的对象
 * @returns {any} 拷贝后的对象
 */
export function deepClone(obj) {
  // 如果是null或undefined，直接返回
  if (obj === null || obj === undefined) {
    return obj;
  }

  // 如果是日期对象，特殊处理
  if (obj instanceof Date) {
    return new Date(obj.getTime());
  }

  // 如果是数组或对象，递归拷贝
  if (typeof obj === 'object') {
    return JSON.parse(JSON.stringify(obj));
  }

  // 其他类型（string、number、boolean等）直接返回
  return obj;
}

/**
 * 防抖函数
 * @param {Function} func - 要执行的函数
 * @param {number} wait - 等待时间（毫秒）
 * @param {boolean} immediate - 是否立即执行
 * @returns {Function} 防抖处理后的函数
 */
export function debounce(func, wait = 300, immediate = false) {
  let timeout; // 定时器ID

  return function executedFunction(...args) {
    // 获取函数执行的上下文
    const context = this;

    // 清除之前的定时器
    if (timeout) {
      clearTimeout(timeout);
    }

    if (immediate && !timeout) {
      // 立即执行模式，且没有正在运行的定时器
      func.apply(context, args);
    }

    // 设置新的定时器
    timeout = setTimeout(() => {
      timeout = null;
      if (!immediate) {
        // 非立即执行模式
        func.apply(context, args);
      }
    }, wait);
  };
}

/**
 * 节流函数
 * @param {Function} func - 要执行的函数
 * @param {number} limit - 时间限制（毫秒）
 * @returns {Function} 节流处理后的函数
 */
export function throttle(func, limit = 300) {
  let inThrottle; // 是否在节流中
  let lastFunc; // 上次待执行的函数
  let lastRan; // 上次执行的时间

  return function executedFunction(...args) {
    const context = this;

    if (!inThrottle) {
      // 不在节流中，直接执行
      func.apply(context, args);
      lastRan = Date.now();
      inThrottle = true;
    } else {
      // 在节流中，清除上次的定时器
      if (lastFunc) {
        clearTimeout(lastFunc);
      }

      // 设置新的定时器，在限制时间后执行
      lastFunc = setTimeout(() => {
        if (Date.now() - lastRan >= limit) {
          func.apply(context, args);
          lastRan = Date.now();
        }
        inThrottle = false;
      }, limit - (Date.now() - lastRan));
    }
  };
}

/**
 * 生成随机字符串
 * @param {number} length - 字符串长度
 * @returns {string} 随机字符串
 */
export function generateRandomString(length = 16) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

/**
 * 生成唯一ID
 * @returns {string} 唯一ID
 */
export function generateUUID() {
  // 使用时间戳和随机数生成唯一ID
  return `${Date.now()}-${generateRandomString(8)}`;
}

/**
 * 验证手机号
 * @param {string} phone - 手机号
 * @returns {boolean} 是否为有效手机号
 */
export function validatePhone(phone) {
  const reg = /^1[3-9]\d{9}$/;
  return reg.test(phone);
}

/**
 * 验证邮箱
 * @param {string} email - 邮箱
 * @returns {boolean} 是否为有效邮箱
 */
export function validateEmail(email) {
  const reg = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
  return reg.test(email);
}

/**
 * 验证工号
 * @param {string} jobNumber - 工号
 * @returns {boolean} 是否为有效工号
 */
export function validateJobNumber(jobNumber) {
  const reg = /^[0-9]{4,20}$/;
  return reg.test(jobNumber);
}

/**
 * 截断字符串（添加省略号）
 * @param {string} str - 原字符串
 * @param {number} maxLength - 最大长度
 * @returns {string} 截断后的字符串
 */
export function truncateString(str, maxLength = 50) {
  if (!str || str.length <= maxLength) {
    return str;
  }
  return str.substring(0, maxLength) + '...';
}

/**
 * 计算相对时间（距离现在过去了多久）
 * @param {Date|string|number} date - 日期
 * @returns {string} 相对时间字符串
 */
export function getRelativeTime(date) {
  if (!(date instanceof Date)) {
    date = new Date(date);
  }

  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  const months = Math.floor(days / 30);
  const years = Math.floor(months / 12);

  if (years > 0) return `${years}年前`;
  if (months > 0) return `${months}个月前`;
  if (days > 0) return `${days}天前`;
  if (hours > 0) return `${hours}小时前`;
  if (minutes > 0) return `${minutes}分钟前`;
  return '刚刚';
}

/**
 * 下载文件
 * @param {Blob|string} data - 文件数据或URL
 * @param {string} filename - 文件名
 */
export function downloadFile(data, filename) {
  // 如果是字符串URL，创建链接下载
  if (typeof data === 'string') {
    const link = document.createElement('a');
    link.href = data;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    return;
  }

  // 如果是Blob对象，创建Blob URL下载
  const url = window.URL.createObjectURL(data);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * 本地存储封装（带过期时间）
 */
export const storage = {
  /**
   * 设置存储项
   * @param {string} key - 键名
   * @param {any} value - 值
   * @param {number} expire - 过期时间（毫秒）
   */
  set(key, value, expire = null) {
    const data = {
      value,
      expire: expire ? Date.now() + expire : null,
    };
    localStorage.setItem(key, JSON.stringify(data));
  },

  /**
   * 获取存储项
   * @param {string} key - 键名
   * @returns {any} 值
   */
  get(key) {
    const str = localStorage.getItem(key);
    if (!str) return null;

    try {
      const data = JSON.parse(str);
      // 检查是否过期
      if (data.expire && Date.now() > data.expire) {
        localStorage.removeItem(key);
        return null;
      }
      return data.value;
    } catch (e) {
      return null;
    }
  },

  /**
   * 移除存储项
   * @param {string} key - 键名
   */
  remove(key) {
    localStorage.removeItem(key);
  },

  /**
   * 清空所有存储项
   */
  clear() {
    localStorage.clear();
  },
};
