import React from 'react';
import clsx from 'clsx';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/styles';
import { Divider, Drawer, Typography } from '@material-ui/core';
import {ImportExport, Dashboard, Home as HomeIcon } from '@material-ui/icons';
import { SidebarNav, Profile } from './components';
import { routePermissions } from 'Routes';
import BarChartIcon from '@material-ui/icons/BarChart';

const useStyles = makeStyles(theme => ({
  drawer: {
    width: 240,
    [theme.breakpoints.up('lg')]: {
      marginTop: 64,
      height: 'calc(100% - 64px)'
    }
  },
  root: {
    backgroundColor: '#F4F6F8',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    padding: theme.spacing(2)
  },
  divider: {
    margin: theme.spacing(2, 0)
  },
  nav: {
    marginBottom: theme.spacing(2)
  }
}));

const Sidebar = props => {
  const { open, variant, onClose, className, ...rest } = props;

  const classes = useStyles();

  const mainApps = [
    {
      title: 'Home',
      href: '/home',
      permissions: routePermissions['home'],
      icon: <HomeIcon />
    },
    {
      title: 'Import',
      href: '/import',
      permissions: routePermissions['import'],
      icon: <ImportExport />
    },
    {
      title: 'Review',
      href: '/review',
      permissions: routePermissions['review'],
      icon: <Dashboard />
    },
    {
      title: 'Train',
      href: '/train',
      permissions: routePermissions['train'],
      icon: <BarChartIcon />
    }
  ];


  return (
    <Drawer
      anchor="left"
      classes={{ paper: classes.drawer }}
      onClose={onClose}
      open={open}
      variant={variant}
    >
      <div
        {...rest}
        className={clsx(classes.root, className)}
      >
      <Profile />
        <Divider className={classes.divider} />
        <Typography>Available Pages</Typography>
        <SidebarNav
          className={classes.nav}
          pages={mainApps}
        />
      </div>
    </Drawer>
  );
};

Sidebar.propTypes = {
  className: PropTypes.string,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  variant: PropTypes.string.isRequired
};

export default Sidebar;
