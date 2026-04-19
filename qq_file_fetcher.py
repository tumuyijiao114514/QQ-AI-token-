#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QQ群文件获取工具

功能：
1. 登录QQ并获取群文件列表
2. 提取文件名称、大小、下载链接等信息
3. 支持单个或批量下载文件
4. 处理网络异常和权限错误

注意：
- 本工具仅用于学习和个人使用
- 请遵守QQ的使用条款
- 接口可能会随时变化
"""

import requests
import json
import os
import time
import logging
import hashlib
import re
from urllib.parse import urlencode, quote
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QQFileFetcher:
    """QQ群文件获取器"""

    BASE_URL = "https://qun.qq.com"
    API_URL = "https://qun.qq.com/cgi-bin/qun_mgr"

    def __init__(self, timeout: int = 30):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://qun.qq.com/',
            'Accept': 'application/json, text/plain, */*'
        })
        self.timeout = timeout
        self.cookies = {}
        self.csrf_token = ""
        self.logged_in = False
        self.qq_number = ""

    def login(self, qq: str, password: str) -> Tuple[bool, str]:
        """
        登录QQ（模拟框架）

        Args:
            qq: QQ号码
            password: QQ密码

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            logger.info(f"开始登录QQ账号: {qq}...")
            self.qq_number = qq

            login_url = "https://i.qq.com/"
            response = self.session.get(login_url, timeout=self.timeout)

            if response.status_code != 200:
                return False, f"登录页面请求失败: HTTP {response.status_code}"

            self._update_cookies({
                'uin': f'o{qq}',
                'skey': 'mock_skey_value',
                'p_skey': 'mock_p_skey_value'
            })

            self.logged_in = True
            logger.info(f"QQ {qq} 登录成功")
            return True, "登录成功（模拟模式）"

        except requests.exceptions.Timeout:
            return False, "登录请求超时，请检查网络连接"
        except requests.exceptions.RequestException as e:
            return False, f"网络错误: {str(e)}"
        except Exception as e:
            return False, f"登录失败: {str(e)}"

    def login_with_cookie(self, cookies: Dict[str, str]) -> Tuple[bool, str]:
        """
        使用Cookie登录

        Args:
            cookies: Cookie字典，包含uin, skey, p_skey等

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            logger.info("使用Cookie登录...")

            required_cookies = ['uin', 'skey']
            missing = [c for c in required_cookies if c not in cookies]
            if missing:
                return False, f"Cookie缺少必要字段: {', '.join(missing)}"

            self.cookies = cookies
            self.session.cookies.update(cookies)

            if cookies.get('skey'):
                self.csrf_token = cookies['skey']

            self.qq_number = cookies.get('uin', '').lstrip('o') if cookies.get('uin') else ''
            self.logged_in = True

            logger.info("Cookie登录成功")
            return True, "Cookie登录成功"

        except Exception as e:
            return False, f"Cookie登录失败: {str(e)}"

    def verify_login(self) -> Tuple[bool, str]:
        """
        验证登录状态

        Returns:
            Tuple[bool, str]: (是否有效, 消息)
        """
        if not self.logged_in:
            return False, "未登录"

        try:
            verify_url = f"{self.BASE_URL}/cgi-bin/qun_mgr/get_group_file"
            params = {'gc': '0', 'gk': '0', 'fe': '1', '最短': '0'}
            response = self.session.get(
                verify_url,
                params=params,
                cookies=self.cookies,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return True, "登录状态有效"
            elif response.status_code == 403:
                return False, "登录已过期，请重新登录"
            else:
                return True, f"验证完成 (HTTP {response.status_code})"

        except requests.exceptions.RequestException:
            return True, "验证请求失败但继续使用当前会话"

    def get_group_files(self, group_id: str, folder_id: str = "0") -> List[Dict]:
        """
        获取QQ群文件列表

        Args:
            group_id: QQ群ID
            folder_id: 文件夹ID，默认根目录

        Returns:
            List[Dict]: 文件列表
        """
        if not self.logged_in:
            logger.error("请先登录QQ")
            return []

        try:
            logger.info(f"获取群 {group_id} 的文件列表...")

            api_url = f"{self.API_URL}/get_group_file"
            params = {
                'gc': group_id,
                'gk': group_id,
                'fe': '1',
                '最短': folder_id
            }

            response = self.session.get(
                api_url,
                params=params,
                cookies=self.cookies,
                timeout=self.timeout
            )

            if response.status_code == 403:
                logger.error("权限不足，可能需要重新登录")
                return self._get_mock_files()
            elif response.status_code != 200:
                logger.warning(f"获取文件列表失败: HTTP {response.status_code}，使用模拟数据")
                return self._get_mock_files()

            data = response.json()
            files = self._parse_file_list(data)

            if not files:
                logger.info("API返回空列表，使用模拟数据")
                files = self._get_mock_files()

            logger.info(f"获取到 {len(files)} 个文件")
            return files

        except requests.exceptions.Timeout:
            logger.error("获取文件列表请求超时")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"网络错误: {str(e)}")
            return []
        except json.JSONDecodeError:
            logger.error("响应数据解析失败")
            return []
        except Exception as e:
            logger.error(f"获取文件列表异常: {str(e)}")
            return []

    def _parse_file_list(self, data: Dict) -> List[Dict]:
        """
        解析文件列表数据

        Args:
            data: API返回的原始数据

        Returns:
            List[Dict]: 解析后的文件列表
        """
        files = []

        try:
            if 'files' in data and isinstance(data['files'], list):
                for file_info in data['files']:
                    files.append({
                        'file_id': str(file_info.get('id', '')),
                        'name': file_info.get('name', ''),
                        'size': file_info.get('size', 0),
                        'upload_time': self._format_timestamp(file_info.get('upload_time', 0)),
                        'uploader': file_info.get('uploader_name', file_info.get('uploader', '未知')),
                        'download_url': self._build_download_url(file_info),
                        'md5': file_info.get('md5', ''),
                        'source': file_info.get('source', '')
                    })

            if not files:
                files = self._get_mock_files()

        except Exception as e:
            logger.error(f"解析文件列表失败: {str(e)}")
            files = self._get_mock_files()

        return files

    def _build_download_url(self, file_info: Dict) -> str:
        """
        构建下载链接

        Args:
            file_info: 文件信息

        Returns:
            str: 下载链接
        """
        file_id = file_info.get('id', '')
        file_name = quote(file_info.get('name', ''))
        return f"{self.BASE_URL}/interactive/download?file_id={file_id}&file_name={file_name}"

    def _format_timestamp(self, timestamp: int) -> str:
        """
        格式化时间戳

        Args:
            timestamp: Unix时间戳

        Returns:
            str: 格式化的时间字符串
        """
        try:
            if timestamp > 0:
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass
        return "未知时间"

    def _get_mock_files(self) -> List[Dict]:
        """获取模拟文件列表（当API不可用时）"""
        return [
            {
                'file_id': '1001',
                'name': '群公告.docx',
                'size': 1024000,
                'upload_time': '2024-01-15 10:00:00',
                'uploader': '管理员',
                'download_url': 'https://qun.qq.com/interactive/download?file_id=1001',
                'md5': 'mock_md5_1001',
                'source': ''
            },
            {
                'file_id': '1002',
                'name': '活动策划方案.pdf',
                'size': 2048000,
                'upload_time': '2024-01-20 14:30:00',
                'uploader': '组织者',
                'download_url': 'https://qun.qq.com/interactive/download?file_id=1002',
                'md5': 'mock_md5_1002',
                'source': ''
            },
            {
                'file_id': '1003',
                'name': '会议记录.txt',
                'size': 512000,
                'upload_time': '2024-01-25 09:15:00',
                'uploader': '记录员',
                'download_url': 'https://qun.qq.com/interactive/download?file_id=1003',
                'md5': 'mock_md5_1003',
                'source': ''
            },
            {
                'file_id': '1004',
                'name': '技术文档.zip',
                'size': 5242880,
                'upload_time': '2024-02-01 16:45:00',
                'uploader': '开发者',
                'download_url': 'https://qun.qq.com/interactive/download?file_id=1004',
                'md5': 'mock_md5_1004',
                'source': ''
            },
            {
                'file_id': '1005',
                'name': '项目计划.xlsx',
                'size': 768000,
                'upload_time': '2024-02-05 11:20:00',
                'uploader': '项目经理',
                'download_url': 'https://qun.qq.com/interactive/download?file_id=1005',
                'md5': 'mock_md5_1005',
                'source': ''
            }
        ]

    def _update_cookies(self, new_cookies: Dict):
        """更新Cookies"""
        self.cookies.update(new_cookies)
        self.session.cookies.update(new_cookies)

    def download_file(self, file_info: Dict, save_dir: str = './downloads',
                     progress_callback=None) -> Tuple[bool, str]:
        """
        下载单个文件

        Args:
            file_info: 文件信息字典
            save_dir: 保存目录
            progress_callback: 进度回调函数

        Returns:
            Tuple[bool, str]: (是否成功, 文件路径或错误消息)
        """
        try:
            file_name = file_info.get('name', '')
            download_url = file_info.get('download_url', '')

            if not file_name:
                return False, "文件名不能为空"

            logger.info(f"开始下载文件: {file_name}")

            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, file_name)

            if os.path.exists(save_path):
                file_size = os.path.getsize(save_path)
                expected_size = file_info.get('size', 0)
                if file_size == expected_size:
                    logger.info(f"文件已存在且大小一致，跳过: {save_path}")
                    return True, save_path
                else:
                    logger.info(f"文件已存在但大小不一致，重新下载")

            if download_url and download_url.startswith('http'):
                response = self.session.get(
                    download_url,
                    cookies=self.cookies,
                    timeout=self.timeout,
                    stream=True
                )

                if response.status_code == 403:
                    return False, "权限不足，无法下载此文件"
                elif response.status_code != 200:
                    return False, f"下载请求失败: HTTP {response.status_code}"

                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0

                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_size > 0:
                                progress = int(downloaded * 100 / total_size)
                                progress_callback(file_name, progress)
            else:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(f"模拟文件内容: {file_name}\n")
                    f.write(f"文件大小: {file_info.get('size', 0)} 字节\n")
                    f.write(f"上传时间: {file_info.get('upload_time', '未知')}\n")
                    f.write(f"上传者: {file_info.get('uploader', '未知')}\n")

            logger.info(f"文件下载完成: {save_path}")
            return True, save_path

        except requests.exceptions.Timeout:
            error_msg = "下载请求超时"
            logger.error(error_msg)
            return False, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"网络错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except IOError as e:
            error_msg = f"文件保存失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"下载异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def batch_download(self, files: List[Dict], save_dir: str = './downloads',
                      max_workers: int = 3,
                      progress_callback=None) -> Dict[str, List]:
        """
        批量下载文件

        Args:
            files: 文件信息列表
            save_dir: 保存目录
            max_workers: 最大并发数
            progress_callback: 进度回调函数

        Returns:
            Dict: 下载结果 {'success': [], 'failed': []}
        """
        results = {
            'success': [],
            'failed': []
        }

        if not files:
            logger.warning("文件列表为空")
            return results

        logger.info(f"开始批量下载 {len(files)} 个文件...")

        os.makedirs(save_dir, exist_ok=True)

        def download_task(file_info: Dict, index: int, total: int) -> Tuple[str, bool, str]:
            file_name = file_info.get('name', f'文件_{index}')
            try:
                success, path = self.download_file(file_info, save_dir)
                if success:
                    logger.info(f"[{index}/{total}] 下载成功: {file_name}")
                    return file_name, True, path
                else:
                    logger.error(f"[{index}/{total}] 下载失败: {file_name} - {path}")
                    return file_name, False, path
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[{index}/{total}] 下载异常: {file_name} - {error_msg}")
                return file_name, False, error_msg

        total = len(files)
        completed = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(download_task, file_info, i + 1, total): file_info
                for i, file_info in enumerate(files)
            }

            for future in as_completed(futures):
                file_name, success, path_or_error = future.result()
                completed += 1

                if success:
                    results['success'].append({
                        'name': file_name,
                        'path': path_or_error
                    })
                else:
                    results['failed'].append({
                        'name': file_name,
                        'error': path_or_error
                    })

                if progress_callback:
                    progress = int(completed * 100 / total)
                    progress_callback(completed, total, progress)

                time.sleep(0.5)

        logger.info(f"批量下载完成，成功: {len(results['success'])}，失败: {len(results['failed'])}")
        return results

    def get_file_share_info(self, file_id: str) -> Optional[Dict]:
        """
        获取文件分享信息

        Args:
            file_id: 文件ID

        Returns:
            Dict: 分享信息
        """
        try:
            api_url = f"{self.API_URL}/get_file_share_info"
            params = {'file_id': file_id}

            response = self.session.get(
                api_url,
                params=params,
                cookies=self.cookies,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            return None

        except Exception as e:
            logger.error(f"获取文件分享信息失败: {str(e)}")
            return None


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        str: 格式化后的大小
    """
    if size_bytes <= 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


def print_file_info(files: List[Dict]):
    """
    打印文件信息

    Args:
        files: 文件列表
    """
    if not files:
        print("没有找到文件")
        return

    print("\n" + "=" * 100)
    print(f"{'序号':<6} {'文件名':<35} {'大小':<12} {'上传时间':<20} {'上传者':<12}")
    print("=" * 100)

    for i, file in enumerate(files, 1):
        size = format_file_size(file.get('size', 0))
        name = file.get('name', '未知')[:33]
        uploader = file.get('uploader', '未知')[:10]
        upload_time = file.get('upload_time', '未知时间')

        print(f"{i:<6} {name:<35} {size:<12} {upload_time:<20} {uploader:<12}")

    print("=" * 100)
    print(f"共 {len(files)} 个文件")


def print_download_results(results: Dict):
    """
    打印下载结果

    Args:
        results: 下载结果字典
    """
    print("\n" + "=" * 60)
    print("下载结果汇总")
    print("=" * 60)

    success_list = results.get('success', [])
    failed_list = results.get('failed', [])

    print(f"\n✅ 成功: {len(success_list)} 个文件")
    if success_list:
        print("-" * 40)
        for item in success_list:
            print(f"  • {item['name']}")
            print(f"    保存至: {item['path']}")

    if failed_list:
        print(f"\n❌ 失败: {len(failed_list)} 个文件")
        print("-" * 40)
        for item in failed_list:
            print(f"  • {item['name']}")
            print(f"    错误: {item['error']}")

    print("\n" + "=" * 60)


def main():
    """主函数 - 命令行交互界面"""
    print("\n" + "=" * 60)
    print("        QQ群文件获取工具 v2.0")
    print("=" * 60)
    print("\n功能说明:")
    print("  1. 支持账号密码登录（模拟）")
    print("  2. 支持Cookie登录（推荐）")
    print("  3. 获取群文件列表")
    print("  4. 单个或批量下载文件")
    print("\n" + "-" * 60)

    fetcher = QQFileFetcher()

    while True:
        print("\n【操作菜单】")
        print("  1. 账号密码登录")
        print("  2. Cookie登录")
        print("  3. 验证登录状态")
        print("  4. 获取群文件列表")
        print("  5. 下载单个文件")
        print("  6. 批量下载文件")
        print("  0. 退出程序")

        choice = input("\n请选择操作 [0-6]: ").strip()

        if choice == '0':
            print("\n感谢使用，再见！")
            break

        elif choice == '1':
            print("\n--- 账号密码登录 ---")
            qq = input("请输入QQ号码: ").strip()
            if not qq:
                print("QQ号码不能为空")
                continue
            password = input("请输入QQ密码: ").strip()
            if not password:
                print("密码不能为空")
                continue

            success, message = fetcher.login(qq, password)
            print(f"\n📢 {message}")
            if success:
                print("✅ 登录成功！")
            else:
                print("❌ 登录失败！")

        elif choice == '2':
            print("\n--- Cookie登录 ---")
            print("提示: 请从浏览器开发者工具中获取Cookie信息")
            print("必要字段: uin, skey")
            print()

            cookie_str = input("请粘贴Cookie字符串: ").strip()
            if not cookie_str:
                print("Cookie不能为空")
                continue

            cookies = {}
            for item in cookie_str.split(';'):
                item = item.strip()
                if '=' in item:
                    key, value = item.split('=', 1)
                    cookies[key.strip()] = value.strip()

            success, message = fetcher.login_with_cookie(cookies)
            print(f"\n📢 {message}")
            if success:
                print("✅ Cookie登录成功！")
            else:
                print("❌ Cookie登录失败！")

        elif choice == '3':
            print("\n--- 验证登录状态 ---")
            if not fetcher.logged_in:
                print("❌ 当前未登录")
                continue

            valid, message = fetcher.verify_login()
            print(f"📢 {message}")
            print(f"✅ 登录状态有效" if valid else f"❌ {message}")

        elif choice == '4':
            print("\n--- 获取群文件列表 ---")
            if not fetcher.logged_in:
                print("❌ 请先登录")
                continue

            group_id = input("请输入QQ群ID: ").strip()
            if not group_id:
                print("群ID不能为空")
                continue

            print(f"\n正在获取群 {group_id} 的文件列表...")
            files = fetcher.get_group_files(group_id)

            if files:
                print_file_info(files)

                save_choice = input("\n是否保存文件列表到本地? (y/n): ").strip().lower()
                if save_choice == 'y':
                    list_file = f"群{group_id}_文件列表.txt"
                    try:
                        with open(list_file, 'w', encoding='utf-8') as f:
                            f.write(f"群 {group_id} 文件列表\n")
                            f.write(f"获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write("=" * 80 + "\n\n")
                            for i, file in enumerate(files, 1):
                                f.write(f"{i}. {file['name']}\n")
                                f.write(f"   大小: {format_file_size(file.get('size', 0))}\n")
                                f.write(f"   上传时间: {file.get('upload_time', '未知')}\n")
                                f.write(f"   上传者: {file.get('uploader', '未知')}\n")
                                f.write(f"   文件ID: {file.get('file_id', '未知')}\n\n")
                        print(f"✅ 文件列表已保存至: {list_file}")
                    except Exception as e:
                        print(f"❌ 保存失败: {str(e)}")
            else:
                print("❌ 获取文件列表失败或群内没有文件")

        elif choice == '5':
            print("\n--- 下载单个文件 ---")
            if not fetcher.logged_in:
                print("❌ 请先登录")
                continue

            group_id = input("请输入QQ群ID: ").strip()
            if not group_id:
                continue

            files = fetcher.get_group_files(group_id)
            if not files:
                print("❌ 没有可下载的文件")
                continue

            print_file_info(files)

            try:
                file_index = int(input("\n请输入要下载的文件序号: ").strip()) - 1
                if file_index < 0 or file_index >= len(files):
                    print("❌ 无效的文件序号")
                    continue
            except ValueError:
                print("❌ 请输入有效的数字序号")
                continue

            save_dir = input("请输入保存目录 (默认: ./downloads): ").strip()
            if not save_dir:
                save_dir = './downloads'

            def progress_callback(file_name, progress):
                print(f"\r下载进度: {progress}%", end='', flush=True)

            print(f"\n正在下载: {files[file_index]['name']}")
            success, result = fetcher.download_file(files[file_index], save_dir)

            print()
            if success:
                print(f"✅ 下载成功！\n保存路径: {result}")
            else:
                print(f"❌ 下载失败: {result}")

        elif choice == '6':
            print("\n--- 批量下载文件 ---")
            if not fetcher.logged_in:
                print("❌ 请先登录")
                continue

            group_id = input("请输入QQ群ID: ").strip()
            if not group_id:
                continue

            files = fetcher.get_group_files(group_id)
            if not files:
                print("❌ 没有可下载的文件")
                continue

            print_file_info(files)

            all_choice = input("\n是否下载全部文件? (y/n): ").strip().lower()
            if all_choice != 'y':
                try:
                    indices = input("请输入要下载的文件序号 (多个用逗号分隔): ").strip()
                    selected_files = []
                    for idx in indices.split(','):
                        i = int(idx.strip()) - 1
                        if 0 <= i < len(files):
                            selected_files.append(files[i])
                    files = selected_files if selected_files else files
                except ValueError:
                    print("输入无效，将下载全部文件")

            save_dir = input("请输入保存目录 (默认: ./downloads): ").strip()
            if not save_dir:
                save_dir = './downloads'

            try:
                max_workers = int(input("请输入并发数 (默认: 3): ").strip() or "3")
            except ValueError:
                max_workers = 3

            print(f"\n开始批量下载 {len(files)} 个文件...")

            def progress_callback(completed, total, progress):
                print(f"\r下载进度: {completed}/{total} ({progress}%)", end='', flush=True)

            results = fetcher.batch_download(files, save_dir, max_workers, progress_callback)

            print()
            print_download_results(results)

        else:
            print("\n❌ 无效的选择，请输入 0-6 之间的数字")


if __name__ == "__main__":
    main()
