/**
 * 将字节大小转换为人类可读的格式
 * @param bytes 字节大小
 * @param decimals 小数位数，默认为1
 * @returns 格式化后的大小字符串，如 "2.1M"、"3G" 等
 */
export function formatFileSize(bytes: number, decimals: number = 1): string {
    if (bytes === 0) return '0B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    // 计算应该使用哪个单位
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    // 转换到对应单位并保留指定的小数位数
    const size = parseFloat((bytes / Math.pow(k, i)).toFixed(decimals));

    // 如果小数部分为0，则去掉小数部分
    const formattedSize = size % 1 === 0 ? Math.floor(size) : size;

    return `${formattedSize}${sizes[i]}`;
}

/**
 * 将字节大小转换为人类可读的格式（简化版本，自动选择合适的小数位数）
 * @param bytes 字节大小
 * @returns 格式化后的大小字符串
 */
export function formatFileSizeAuto(bytes: number): string {
    if (bytes === 0) return '0B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const size = bytes / Math.pow(k, i);

    // 根据大小自动选择小数位数
    let decimals = 1;
    if (size >= 100) decimals = 0;
    else if (size >= 10) decimals = 1;
    else decimals = 2;

    const formattedSize = parseFloat(size.toFixed(decimals));
    const finalSize = formattedSize % 1 === 0 ? Math.floor(formattedSize) : formattedSize;

    return `${finalSize}${sizes[i]}`;
}

/**
 * 将字节大小转换为人类可读的格式（中文版本）
 * @param bytes 字节大小
 * @param decimals 小数位数，默认为1
 * @returns 格式化后的大小字符串，如 "2.1兆"、"3吉" 等
 */
export function formatFileSizeChinese(bytes: number, decimals: number = 1): string {
    if (bytes === 0) return '0字节';

    const k = 1024;
    // const sizes = ['字节', '千字节', '兆字节', '吉字节', '太字节', '拍字节', '艾字节', '泽字节', '尧字节'];
    const shortSizes = ['字节', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const size = parseFloat((bytes / Math.pow(k, i)).toFixed(decimals));

    const formattedSize = size % 1 === 0 ? Math.floor(size) : size;

    return `${formattedSize}${shortSizes[i]}`;
}
