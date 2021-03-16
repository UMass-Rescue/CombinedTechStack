import React from 'react';
import PropTypes from 'prop-types';
import clsx from 'clsx';
import { makeStyles } from '@material-ui/styles';
import { Typography } from '@material-ui/core';

const useStyles = makeStyles(theme => ({
  root: {
    padding: theme.spacing(4)
  },
  newFooter: {
    position: 'fixed',
    bottom: '1em',
    left: '1em'
  }
}));

const Footer = props => {
  const { className, ...rest } = props;

  const classes = useStyles();

  return (
    // <div className={classes.newFooter}>
    //   <div
    //     {...rest}
    //     className={clsx(classes.root, className)}
    //   >
    //     <Typography variant="body1">
    //       &copy;{' '} Rescue Lab
    //     </Typography>
    //   </div>
    // </div>
    <div>
      
    </div>
  );
};

Footer.propTypes = {
  className: PropTypes.string
};

export default Footer;
