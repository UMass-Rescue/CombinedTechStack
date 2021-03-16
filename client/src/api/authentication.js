import { api, baseurl } from './api';
import axios from 'axios';

let Auth = {
  isAuthenticated: localStorage.getItem('isAuthenticated') ? JSON.parse(localStorage.getItem('isAuthenticated')) : false,
  token: localStorage.getItem('token') ? localStorage.getItem('token') : '',
  user: localStorage.getItem('userData') ? JSON.parse(localStorage.getItem('userData')) : {},

  getUsername() {
    if (Auth.isAuthenticated) {
      return Auth.user['username'];
    }
    return '';
  },

  getRoles() {
    if (Auth.isAuthenticated) {
      return Auth.user['roles'];
    }
    return [];
  },

  async validateCredentials() {
    if (!Auth.isAuthenticated) {
      return false;
    }

    try {
      await axios.request({
        method: 'get',
        url: baseurl + api['auth_status'],
        headers: { Authorization: 'Bearer ' + Auth.token}
      });
      Auth.isAuthenticated = true;
      return true;

    } catch (e) {
      Auth.logout();
      return false;
    }
  },
  logout() {
    Auth.isAuthenticated = false;
    Auth.token = '';
    Auth.user = {};
    localStorage.removeItem('token');
    localStorage.removeItem('userData');
    localStorage.removeItem('isAuthenticated');
  },
  getUserData() {
    if (!Auth.isAuthenticated) {
      return {};
    }
    axios.request({
      method: 'get',
      url: baseurl + api['auth_profile'],
      headers: { Authorization: 'Bearer ' + Auth.token}
    }).then((response) => {
        return response.data;
    });
  }
};

// module.exports = Auth;
export default Auth;