import React, { useState } from 'react';
import axios from 'axios';
import { makeStyles } from '@material-ui/styles';
import { Box, Grid, Card, CardContent, Button, Typography, TextField } from '@material-ui/core';
import { useHistory } from 'react-router-dom'
import { api, Auth, baseurl } from 'api';

const useStyles = makeStyles(theme => ({
    root: {
        padding: theme.spacing(4),
        overflowX: 'hidden',
    },
    loginTopPadding: {
        paddingTop: '20vh',
    },
    spacingGridRow: {
      marginTop: '1vh',
    },
}));


const Login = () => {
    const classes = useStyles();


    // Set image total from localstorage
    const [errorMessage, setErrorMessage] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const history = useHistory();


    function sendToHome() {
        history.push('/home');
    }

    function pressEnterToLogin(event) {
        if (event.key === 'Enter') {
            attemptLogin();
        }
    }

    function attemptLogin() {
        let formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        const config = {
            headers: {
                'content-type': 'multipart/form-data'
            }
        }
        axios.post(baseurl + api['login'], formData, config).then((response) => {
            if ('status' in response.data) {
                Auth.token = response.data['access_token'];
                Auth.isAuthenticated = true;
                localStorage.setItem('token', Auth.token);
                localStorage.setItem('isAuthenticated', 'true')

                axios.request({
                    method: 'get',
                    url: baseurl + api['auth_profile'],
                    headers: { Authorization: 'Bearer ' + Auth.token}
                }).then((response) => {
                    localStorage.setItem('userData', JSON.stringify(response.data));
                    Auth.user = response.data;
                    sendToHome();
                }).catch((error) => {
                    console.log(error);
                    setErrorMessage('Unable to log in at this time.');
                })

            } else {
                setErrorMessage(response.data['detail']);
            }
        }, (error) => {
            if (error.status && 'detail' in error.response.data) {
                setErrorMessage(error.response.data['detail']);
            } else {
                setErrorMessage('Unable to log in at this time.');
            }
        });
    }
    

    return (
        <div className={classes.root}>
            <Box display={{ xs: 'none', sm: 'block' }} className={classes.loginTopPadding} xs={12}>

            </Box>

            <Grid
                container
                justify="center"
                direction="row"
                spacing={3}
                display="flex"

            >

                <Grid item xs={4}>

                </Grid>

                <Grid item xs={4}>
                    <Card>
                        <CardContent>
                            <Grid container spacing={1} alignItems="flex-end">
                                {/* Row 1 */}
                                <Grid xs={2} item></Grid>
                                <Grid item xs={8}>
                                    <Typography variant={"h2"}>Sign In</Typography>
                                </Grid>
                                <Grid xs={2} item></Grid>
                                <Grid item xs={12} className={classes.spacingGridRow} />


                                {/* Row 2 */}
                                <Grid xs={2} item></Grid>
                                <Grid item xs={8}>
                                    <TextField 
                                        variant="outlined" 
                                        fullWidth={true} 
                                        size="medium" 
                                        id="username" 
                                        label="Username" 
                                        onChange={(event) => setUsername(event.target.value)}
                                        onKeyDown={(e) => pressEnterToLogin(e)}
                                    />
                                </Grid>
                                <Grid xs={2} item></Grid>
                                <Grid item xs={12} className={classes.spacingGridRow} />


                                {/* Row 3 */}
                                <Grid xs={2} item></Grid>
                                <Grid item xs={8}>
                                    <TextField 
                                        variant="outlined" 
                                        fullWidth={true} 
                                        size="medium" 
                                        id="password" 
                                        type="password"
                                        label="Password" 
                                        onChange={(event) => setPassword(event.target.value)}
                                        onKeyDown={(e) => pressEnterToLogin(e)}
                                    />                                
                                </Grid>
                                <Grid xs={2} item></Grid>
                                <Grid item xs={12} className={classes.spacingGridRow} />

                                <Grid xs={2} item></Grid>
                                <Grid item xs={8}>
                                    <Typography variant="subtitle1" color='error'>{errorMessage}</Typography>
                                </Grid>
                                <Grid xs={2} item></Grid>

                                {/* Row 4 */}
                                <Grid xs={2} item></Grid>
                                <Grid item xs={8}>
                                    <Button
                                        variant="contained" color="secondary" type="submit"
                                        fullWidth={true}
                                        onClick={attemptLogin}
                                    >
                                        Login
                                    </Button>
                                </Grid>
                                <Grid xs={2} item></Grid>

                            </Grid>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={4}>

                </Grid>

            </Grid>
        </div>
    );
};

export default Login;
