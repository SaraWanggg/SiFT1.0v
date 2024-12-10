# client.py

import sys, os, socket, cmd, getpass
from Crypto.Hash import SHA256
from siftprotocols.siftmtp import SiFT_MTP, SiFT_MTP_Error
from siftprotocols.siftlogin import SiFT_LOGIN, SiFT_LOGIN_Error
from siftprotocols.siftcmd import SiFT_CMD, SiFT_CMD_Error
from siftprotocols.siftupl import SiFT_UPL, SiFT_UPL_Error
from siftprotocols.siftdnl import SiFT_DNL, SiFT_DNL_Error
from Crypto.PublicKey import RSA

# ----------- CONFIG -------------
server_ip = '127.0.0.1'  # localhost
server_port = 5152
# --------------------------------

class SiFTShell(cmd.Cmd):
    intro = 'Client shell for the SiFT protocol. Type help or ? to list commands.\n'
    prompt = '(sift) '
    file = None

    # ----- commands -----
    def do_pwd(self, arg):
        'Print current working directory on the server: pwd'
        cmd_req_struct = {'command': cmdp.cmd_pwd}
        try:
            cmd_res_struct = cmdp.send_command(cmd_req_struct)
        except SiFT_CMD_Error as e:
            print('SiFT_CMD_Error:', e.err_msg)
            if 'Verification of command response failed' in e.err_msg:
                print('Verification failed. Closing connection.')
                sckt.close()
                return True  # Exit the command loop
        else:
            if cmd_res_struct['result_1'] == cmdp.res_failure:
                print('Remote_Error:', cmd_res_struct['result_2'])
            else:
                print(cmd_res_struct['result_2'])

    def do_ls(self, arg):
        'List content of the current working directory on the server: ls'
        cmd_req_struct = {'command': cmdp.cmd_lst}
        try:
            cmd_res_struct = cmdp.send_command(cmd_req_struct)
        except SiFT_CMD_Error as e:
            print('SiFT_CMD_Error:', e.err_msg)
            if 'Verification of command response failed' in e.err_msg:
                print('Verification failed. Closing connection.')
                sckt.close()
                return True
        else:
            if cmd_res_struct['result_1'] == cmdp.res_failure:
                print('Remote_Error:', cmd_res_struct['result_2'])
            else:
                if cmd_res_struct['result_2']:
                    print(cmd_res_struct['result_2'])
                else:
                    print('[empty]')

    def do_cd(self, arg):
        'Change the current working directory on the server: cd <dirname>'
        dirname = arg.strip()
        cmd_req_struct = {'command': cmdp.cmd_chd, 'param_1': dirname}
        try:
            cmd_res_struct = cmdp.send_command(cmd_req_struct)
        except SiFT_CMD_Error as e:
            print('SiFT_CMD_Error:', e.err_msg)
            if 'Verification of command response failed' in e.err_msg:
                print('Verification failed. Closing connection.')
                sckt.close()
                return True
        else:
            if cmd_res_struct['result_1'] == cmdp.res_failure:
                print('Remote_Error:', cmd_res_struct['result_2'])

    def do_mkd(self, arg):
        'Create a new directory in the current working directory on the server: mkd <dirname>'
        dirname = arg.strip()
        cmd_req_struct = {'command': cmdp.cmd_mkd, 'param_1': dirname}
        try:
            cmd_res_struct = cmdp.send_command(cmd_req_struct)
        except SiFT_CMD_Error as e:
            print('SiFT_CMD_Error:', e.err_msg)
            if 'Verification of command response failed' in e.err_msg:
                print('Verification failed. Closing connection.')
                sckt.close()
                return True
        else:
            if cmd_res_struct['result_1'] == cmdp.res_failure:
                print('Remote_Error:', cmd_res_struct['result_2'])

    def do_del(self, arg):
        'Delete the given file or (empty) directory on the server: del <filename> or del <dirname>'
        fdname = arg.strip()
        cmd_req_struct = {'command': cmdp.cmd_del, 'param_1': fdname}
        try:
            cmd_res_struct = cmdp.send_command(cmd_req_struct)
        except SiFT_CMD_Error as e:
            print('SiFT_CMD_Error:', e.err_msg)
            if 'Verification of command response failed' in e.err_msg:
                print('Verification failed. Closing connection.')
                sckt.close()
                return True
        else:
            if cmd_res_struct['result_1'] == cmdp.res_failure:
                print('Remote_Error:', cmd_res_struct['result_2'])

    def do_upl(self, arg):
        'Upload the given file to the server: upl <filename>'
        filepath = arg.strip()
        if not os.path.isfile(filepath):
            print('Local_Error:', filepath, 'does not exist or is not a file')
            return
        else:
            with open(filepath, 'rb') as f:
                hash_fn = SHA256.new()
                file_size = 0
                while True:
                    chunk = f.read(1024)
                    if not chunk:
                        break
                    file_size += len(chunk)
                    hash_fn.update(chunk)
                file_hash = hash_fn.digest()

            cmd_req_struct = {
                'command': cmdp.cmd_upl,
                'param_1': os.path.basename(filepath),
                'param_2': file_size,
                'param_3': file_hash
            }

            try:
                cmd_res_struct = cmdp.send_command(cmd_req_struct)
            except SiFT_CMD_Error as e:
                print('SiFT_CMD_Error:', e.err_msg)
                if 'Verification of command response failed' in e.err_msg:
                    print('Verification failed. Closing connection.')
                    sckt.close()
                    return True
            else:
                if cmd_res_struct['result_1'] == cmdp.res_reject:
                    print('Remote_Error:', cmd_res_struct['result_2'])
                else:
                    print('Starting upload...')
                    uplp = SiFT_UPL(mtp)
                    try:
                        uplp.handle_upload_client(filepath)
                    except SiFT_UPL_Error as e:
                        print('Upload_Error:', e.err_msg)
                    else:
                        print('Upload completed.')

    def do_dnl(self, arg):
        'Download the given file from the server: dnl <filename>'
        filename = arg.strip()
        cmd_req_struct = {'command': cmdp.cmd_dnl, 'param_1': filename}
        try:
            cmd_res_struct = cmdp.send_command(cmd_req_struct)
        except SiFT_CMD_Error as e:
            print('SiFT_CMD_Error:', e.err_msg)
            if 'Verification of command response failed' in e.err_msg:
                print('Verification failed. Closing connection.')
                sckt.close()
                return True
        else:
            if cmd_res_struct['result_1'] == cmdp.res_reject:
                print('Remote_Error:', cmd_res_struct['result_2'])
            else:
                print('File size:', cmd_res_struct['result_2'])
                print('File hash:', cmd_res_struct['result_3'].hex())
                yn = ''
                while yn.lower() not in ('y', 'yes', 'n', 'no'):
                    yn = input('Do you want to proceed? (y/n) ')
                if yn.lower() in ('y', 'yes'):
                    print('Starting download...')
                    dnlp = SiFT_DNL(mtp)
                    try:
                        file_hash = dnlp.handle_download_client(filename)
                    except SiFT_DNL_Error as e:
                        print('Download_Error:', e.err_msg)
                    else:
                        if file_hash != cmd_res_struct['result_3']:
                            print('Warning: File hash mismatch!')
                        print('Download completed.')
                else:
                    print('Download canceled.')
                    dnlp = SiFT_DNL(mtp)
                    try:
                        dnlp.cancel_download_client()
                    except SiFT_DNL_Error as e:
                        print('Download_Error:', e.err_msg)
                    else:
                        print('Download canceled.')

    def do_bye(self, arg):
        'Exit from the client shell: bye'
        print('Closing connection with server...')
        sckt.close()
        return True

# --------------------------------------
if __name__ == '__main__':
    try:
        sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sckt.connect((server_ip, server_port))
    except Exception as e:
        print('Network_Error: Cannot open connection to the server:', str(e))
        sys.exit(1)
    else:
        print('Connection to server established on ' + server_ip + ':' + str(server_port))

    mtp = SiFT_MTP(sckt)
    loginp = SiFT_LOGIN(mtp)

    # Load server's public key
    try:
        with open('server_public_key.pem', 'rb') as f:
            server_public_key = RSA.import_key(f.read())
    except Exception as e:
        print('Error loading server public key:', str(e))
        sys.exit(1)

    loginp.set_server_public_key(server_public_key)

    print()
    username = input('   Username: ')
    password = getpass.getpass('   Password: ')
    print()

    try:
        loginp.handle_login_client(username, password)
    except SiFT_LOGIN_Error as e:
        print('SiFT_LOGIN_Error:', e.err_msg)
        sys.exit(1)

    cmdp = SiFT_CMD(mtp)

    SiFTShell().cmdloop()
