/**
 * 日期工具类
 * 提供常用的日期处理功能
 */
export class DateUtil {
    /**
     * 格式化日期为指定格式
     * @param date 日期对象或日期字符串
     * @param format 格式化字符串，支持以下占位符：
     * - YYYY: 4位年份
     * - YY: 2位年份
     * - MM: 2位月份
     * - M: 1位月份
     * - DD: 2位日期
     * - D: 1位日期
     * - HH: 2位小时（24小时制）
     * - H: 1位小时（24小时制）
     * - hh: 2位小时（12小时制）
     * - h: 1位小时（12小时制）
     * - mm: 2位分钟
     * - m: 1位分钟
     * - ss: 2位秒
     * - s: 1位秒
     * - SSS: 3位毫秒
     * - A: AM/PM
     * - a: am/pm
     * @returns 格式化后的日期字符串
     */
    static format(date: Date | string | number, format: string = 'YYYY-MM-DD HH:mm:ss'): string {
        const d = new Date(date);
        if (isNaN(d.getTime())) {
            throw new Error('Invalid date');
        }

        const year = d.getFullYear();
        const month = d.getMonth() + 1;
        const day = d.getDate();
        const hours = d.getHours();
        const minutes = d.getMinutes();
        const seconds = d.getSeconds();
        const milliseconds = d.getMilliseconds();

        const pad = (num: number, length: number = 2): string => {
            return num.toString().padStart(length, '0');
        };

        return format
            .replace(/YYYY/g, year.toString())
            .replace(/YY/g, year.toString().slice(-2))
            .replace(/MM/g, pad(month))
            .replace(/M/g, month.toString())
            .replace(/DD/g, pad(day))
            .replace(/D/g, day.toString())
            .replace(/HH/g, pad(hours))
            .replace(/H/g, hours.toString())
            .replace(/hh/g, pad(hours % 12 || 12))
            .replace(/h/g, (hours % 12 || 12).toString())
            .replace(/mm/g, pad(minutes))
            .replace(/m/g, minutes.toString())
            .replace(/ss/g, pad(seconds))
            .replace(/s/g, seconds.toString())
            .replace(/SSS/g, pad(milliseconds, 3))
            .replace(/A/g, hours >= 12 ? 'PM' : 'AM')
            .replace(/a/g, hours >= 12 ? 'pm' : 'am');
    }

    /**
     * 解析日期字符串为Date对象
     * @param dateString 日期字符串
     * @param format 日期格式（可选）
     * @returns Date对象
     */
    static parse(dateString: string, format?: string): Date {
        if (format) {
            // 根据格式解析日期
            return this.parseByFormat(dateString, format);
        }

        const date = new Date(dateString);
        if (isNaN(date.getTime())) {
            throw new Error('Invalid date string');
        }
        return date;
    }

    /**
     * 根据格式解析日期字符串
     * @param dateString 日期字符串
     * @param format 日期格式
     * @returns Date对象
     */
    private static parseByFormat(dateString: string, format: string): Date {
        // 简单的格式解析实现
        const regex = format
            .replace(/YYYY/g, '(\\d{4})')
            .replace(/YY/g, '(\\d{2})')
            .replace(/MM/g, '(\\d{2})')
            .replace(/M/g, '(\\d{1,2})')
            .replace(/DD/g, '(\\d{2})')
            .replace(/D/g, '(\\d{1,2})')
            .replace(/HH/g, '(\\d{2})')
            .replace(/H/g, '(\\d{1,2})')
            .replace(/mm/g, '(\\d{2})')
            .replace(/m/g, '(\\d{1,2})')
            .replace(/ss/g, '(\\d{2})')
            .replace(/s/g, '(\\d{1,2})');

        const match = dateString.match(new RegExp(regex));
        if (!match) {
            throw new Error('Date string does not match format');
        }

        // 这里需要根据具体格式实现解析逻辑
        // 简化实现，直接使用原生Date解析
        return new Date(dateString);
    }

    /**
     * 获取当前时间戳
     * @returns 当前时间戳（毫秒）
     */
    static now(): number {
        return Date.now();
    }

    /**
     * 获取相对时间描述
     * @param date 日期对象或日期字符串
     * @param baseDate 基准日期，默认为当前时间
     * @returns 相对时间描述
     */
    static fromNow(date: Date | string | number, baseDate: Date | string | number = new Date()): string {
        const target = new Date(date);
        const base = new Date(baseDate);
        const diff = base.getTime() - target.getTime();
        const absDiff = Math.abs(diff);

        const minute = 60 * 1000;
        const hour = 60 * minute;
        const day = 24 * hour;
        const week = 7 * day;
        const month = 30 * day;
        const year = 365 * day;

        if (absDiff < minute) {
            return diff >= 0 ? '刚刚' : '马上';
        } else if (absDiff < hour) {
            const minutes = Math.floor(absDiff / minute);
            return diff >= 0 ? `${minutes}分钟前` : `${minutes}分钟后`;
        } else if (absDiff < day) {
            const hours = Math.floor(absDiff / hour);
            return diff >= 0 ? `${hours}小时前` : `${hours}小时后`;
        } else if (absDiff < week) {
            const days = Math.floor(absDiff / day);
            return diff >= 0 ? `${days}天前` : `${days}天后`;
        } else if (absDiff < month) {
            const weeks = Math.floor(absDiff / week);
            return diff >= 0 ? `${weeks}周前` : `${weeks}周后`;
        } else if (absDiff < year) {
            const months = Math.floor(absDiff / month);
            return diff >= 0 ? `${months}个月前` : `${months}个月后`;
        } else {
            const years = Math.floor(absDiff / year);
            return diff >= 0 ? `${years}年前` : `${years}年后`;
        }
    }

    /**
     * 获取日期是否为今天
     * @param date 日期对象或日期字符串
     * @returns 是否为今天
     */
    static isToday(date: Date | string | number): boolean {
        const target = new Date(date);
        const today = new Date();
        return this.isSameDay(target, today);
    }

    /**
     * 获取日期是否为昨天
     * @param date 日期对象或日期字符串
     * @returns 是否为昨天
     */
    static isYesterday(date: Date | string | number): boolean {
        const target = new Date(date);
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        return this.isSameDay(target, yesterday);
    }

    /**
     * 获取日期是否为明天
     * @param date 日期对象或日期字符串
     * @returns 是否为明天
     */
    static isTomorrow(date: Date | string | number): boolean {
        const target = new Date(date);
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        return this.isSameDay(target, tomorrow);
    }

    /**
     * 判断两个日期是否为同一天
     * @param date1 第一个日期
     * @param date2 第二个日期
     * @returns 是否为同一天
     */
    static isSameDay(date1: Date | string | number, date2: Date | string | number): boolean {
        const d1 = new Date(date1);
        const d2 = new Date(date2);
        return d1.getFullYear() === d2.getFullYear() &&
            d1.getMonth() === d2.getMonth() &&
            d1.getDate() === d2.getDate();
    }

    /**
     * 获取日期所在周的开始日期（周一）
     * @param date 日期对象或日期字符串
     * @returns 周开始日期
     */
    static startOfWeek(date: Date | string | number): Date {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? -6 : 1); // 调整为周一为开始
        return new Date(d.setDate(diff));
    }

    /**
     * 获取日期所在周的结束日期（周日）
     * @param date 日期对象或日期字符串
     * @returns 周结束日期
     */
    static endOfWeek(date: Date | string | number): Date {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? 0 : 7); // 调整为周日为结束
        return new Date(d.setDate(diff));
    }

    /**
     * 获取日期所在月的开始日期
     * @param date 日期对象或日期字符串
     * @returns 月开始日期
     */
    static startOfMonth(date: Date | string | number): Date {
        const d = new Date(date);
        return new Date(d.getFullYear(), d.getMonth(), 1);
    }

    /**
     * 获取日期所在月的结束日期
     * @param date 日期对象或日期字符串
     * @returns 月结束日期
     */
    static endOfMonth(date: Date | string | number): Date {
        const d = new Date(date);
        return new Date(d.getFullYear(), d.getMonth() + 1, 0);
    }

    /**
     * 获取日期所在年的开始日期
     * @param date 日期对象或日期字符串
     * @returns 年开始日期
     */
    static startOfYear(date: Date | string | number): Date {
        const d = new Date(date);
        return new Date(d.getFullYear(), 0, 1);
    }

    /**
     * 获取日期所在年的结束日期
     * @param date 日期对象或日期字符串
     * @returns 年结束日期
     */
    static endOfYear(date: Date | string | number): Date {
        const d = new Date(date);
        return new Date(d.getFullYear(), 11, 31);
    }

    /**
     * 添加天数
     * @param date 日期对象或日期字符串
     * @param days 要添加的天数
     * @returns 新的日期对象
     */
    static addDays(date: Date | string | number, days: number): Date {
        const d = new Date(date);
        d.setDate(d.getDate() + days);
        return d;
    }

    /**
     * 添加月数
     * @param date 日期对象或日期字符串
     * @param months 要添加的月数
     * @returns 新的日期对象
     */
    static addMonths(date: Date | string | number, months: number): Date {
        const d = new Date(date);
        d.setMonth(d.getMonth() + months);
        return d;
    }

    /**
     * 添加年数
     * @param date 日期对象或日期字符串
     * @param years 要添加的年数
     * @returns 新的日期对象
     */
    static addYears(date: Date | string | number, years: number): Date {
        const d = new Date(date);
        d.setFullYear(d.getFullYear() + years);
        return d;
    }

    /**
     * 获取两个日期之间的天数差
     * @param date1 第一个日期
     * @param date2 第二个日期
     * @returns 天数差
     */
    static diffInDays(date1: Date | string | number, date2: Date | string | number): number {
        const d1 = new Date(date1);
        const d2 = new Date(date2);
        const diffTime = Math.abs(d2.getTime() - d1.getTime());
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }

    /**
     * 获取两个日期之间的月数差
     * @param date1 第一个日期
     * @param date2 第二个日期
     * @returns 月数差
     */
    static diffInMonths(date1: Date | string | number, date2: Date | string | number): number {
        const d1 = new Date(date1);
        const d2 = new Date(date2);
        return (d2.getFullYear() - d1.getFullYear()) * 12 + (d2.getMonth() - d1.getMonth());
    }

    /**
     * 获取两个日期之间的年数差
     * @param date1 第一个日期
     * @param date2 第二个日期
     * @returns 年数差
     */
    static diffInYears(date1: Date | string | number, date2: Date | string | number): number {
        const d1 = new Date(date1);
        const d2 = new Date(date2);
        return d2.getFullYear() - d1.getFullYear();
    }

    /**
     * 获取日期的年龄
     * @param birthDate 出生日期
     * @param currentDate 当前日期，默认为当前时间
     * @returns 年龄
     */
    static getAge(birthDate: Date | string | number, currentDate: Date | string | number = new Date()): number {
        const birth = new Date(birthDate);
        const current = new Date(currentDate);
        let age = current.getFullYear() - birth.getFullYear();
        const monthDiff = current.getMonth() - birth.getMonth();

        if (monthDiff < 0 || (monthDiff === 0 && current.getDate() < birth.getDate())) {
            age--;
        }

        return age;
    }

    /**
     * 获取日期是否为闰年
     * @param date 日期对象或日期字符串
     * @returns 是否为闰年
     */
    static isLeapYear(date: Date | string | number): boolean {
        const year = new Date(date).getFullYear();
        return (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
    }

    /**
     * 获取月份的天数
     * @param date 日期对象或日期字符串
     * @returns 月份天数
     */
    static getDaysInMonth(date: Date | string | number): number {
        const d = new Date(date);
        return new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
    }

    /**
     * 获取日期的星期几
     * @param date 日期对象或日期字符串
     * @param locale 语言环境，默认为中文
     * @returns 星期几
     */
    static getDayOfWeek(date: Date | string | number, locale: string = 'zh-CN'): string {
        const d = new Date(date);
        return d.toLocaleDateString(locale, { weekday: 'long' });
    }

    /**
     * 获取日期的星期几（数字）
     * @param date 日期对象或日期字符串
     * @returns 星期几的数字（0-6，0为周日）
     */
    static getDayOfWeekNumber(date: Date | string | number): number {
        return new Date(date).getDay();
    }

    /**
     * 获取友好的日期显示
     * @param date 日期对象或日期字符串
     * @returns 友好的日期字符串
     */
    static getFriendlyDate(date: Date | string | number): string {
        const target = new Date(date);
        const now = new Date();

        if (this.isToday(target)) {
            return '今天';
        } else if (this.isYesterday(target)) {
            return '昨天';
        } else if (this.isTomorrow(target)) {
            return '明天';
        } else {
            const diffDays = this.diffInDays(target, now);
            if (diffDays < 7) {
                return `${diffDays}天前`;
            } else if (diffDays < 30) {
                const weeks = Math.floor(diffDays / 7);
                return `${weeks}周前`;
            } else {
                return this.format(target, 'YYYY-MM-DD');
            }
        }
    }

    /**
     * 获取时间范围描述
     * @param startDate 开始日期
     * @param endDate 结束日期
     * @returns 时间范围描述
     */
    static getDateRangeDescription(startDate: Date | string | number, endDate: Date | string | number): string {
        const start = new Date(startDate);
        const end = new Date(endDate);

        if (this.isSameDay(start, end)) {
            return this.format(start, 'YYYY年MM月DD日');
        } else if (start.getFullYear() === end.getFullYear()) {
            return `${this.format(start, 'MM月DD日')} - ${this.format(end, 'MM月DD日')}`;
        } else {
            return `${this.format(start, 'YYYY年MM月DD日')} - ${this.format(end, 'YYYY年MM月DD日')}`;
        }
    }
}

// 导出常用的格式化函数
export const formatDate = (date: Date | string | number, format?: string) => DateUtil.format(date, format);
export const fromNow = (date: Date | string | number) => DateUtil.fromNow(date);
export const isToday = (date: Date | string | number) => DateUtil.isToday(date);
export const getFriendlyDate = (date: Date | string | number) => DateUtil.getFriendlyDate(date);
