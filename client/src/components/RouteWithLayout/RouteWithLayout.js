import React, { useEffect, useState } from 'react';
import { Route, Redirect } from 'react-router-dom';
import PropTypes from 'prop-types';
import { Auth } from 'api';


async function checkAuth(useAuth, permissions) {

  if (useAuth) {
    await Auth.validateCredentials();

    // If user is not logged in
    if (!Auth.isAuthenticated) {
      return 'login';
    // If user is logged in, and the permission type allows the user to access page
    } else if (
      permissions.includes('*') ||      
      permissions.some(item => Auth.getRoles().includes(item))
    ) {
      return 'none';
    // If user is logged in but does not have permissions for the page
    } else {
      return 'home';
    }
  }

  return 'none';
}

const RouteWithLayout = props => {
  const { layout: Layout, component: Component, useAuth: boolean, permissions: array, ...rest } = props;

  const useAuth = props.useAuth;
  let permissions = props.permissions;
  const [pageRedirect, setPageRedirect] = useState('pending');

  useEffect(() => {
    checkAuth(useAuth, permissions).then((res) => {
      setPageRedirect(res);
    });
    
  }, [permissions, useAuth]);
  
  function getComponentToRender(matchProps) {
    if (pageRedirect === 'login') {
      return <Redirect to='/login' />
    }

    if (pageRedirect === 'home') {
      return <Redirect to='/home' />
    }

    if (pageRedirect === 'pending') {
      return <div id='pending-redirect'> Please stand by...</div>
    }

    if (pageRedirect === 'none') {
      return (
        <Layout>
          <Component {...matchProps} />
        </Layout>
      )
    }
  }

  return (
    <Route
      {...rest}
      render={(matchProps) => getComponentToRender(matchProps)}
    />
  );
};

RouteWithLayout.propTypes = {
  component: PropTypes.any.isRequired,
  layout: PropTypes.any.isRequired,
  path: PropTypes.string,
  useAuth: PropTypes.bool,
  permissions: PropTypes.array,
};

export default RouteWithLayout;
