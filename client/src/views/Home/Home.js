import React, { useEffect, useState } from 'react';
import { makeStyles } from '@material-ui/styles';
import { Box, Button, Card, CardContent, Grid, Snackbar, TableContainer, TableHead, Typography } from '@material-ui/core';
import Table from "@material-ui/core/Table";
import TableRow from "@material-ui/core/TableRow";
import ButtonGroup from '@material-ui/core/ButtonGroup';
import TableCell from "@material-ui/core/TableCell";
import TableBody from "@material-ui/core/TableBody";
import Axios from 'axios';
import MenuItem from '@material-ui/core/MenuItem';
import { api, Auth, baseurl } from 'api';
import Alert from '@material-ui/lab/Alert';
import AddIcon from '@material-ui/icons/Add';
import TextField from '@material-ui/core/TextField';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';

const useStyles = makeStyles(theme => ({
    root: {
        padding: theme.spacing(4),
        overflowX: 'hidden',
    },
    loginTopPadding: {
        paddingTop: '20vh',
    },
    loginGrid1: {
        // backgroundColor: 'black',
    },
    loginGrid2: {
        // backgroundColor: 'red',
    },
    apiKeyListContainer: {
        width: '100%',
        height: '55vh',
        borderRadius: '0.6em',
    },
    apiKeyListTable: {
        overflow: 'auto',
        maxHeight: '45vh',
    },
}));


const Home = () => {
    const classes = useStyles();

    const [apiKeys, setApiKeys] = useState([]); // API Keys Associated with User
    const [newKeyDetail, setNewKeyDetail] = useState('');
    const [newKeyType, setNewKeyType] = useState('');
    
    const [successSnackbarOpen, setSuccessSnackbarOpen] = useState(false);
    const [successSnackbarMessage, setSuccessSnackbarMessage] = useState(false);

    const [newKeyDialogOpen, setNewKeyDialogOpen] = useState(false);



    useEffect(() => {
       getAPIKeys();
    }, []);

    function getAPIKeys() {
        Axios.request({ 
            method: 'get', 
            url: baseurl + api['api_key_list'] + '?nocache=' + new Date().getTime(), 
            headers: { Authorization: 'Bearer ' + Auth.token } }
        ).then((response) => {
            setApiKeys(response.data['keys']);
        }, (error) => {
            console.log('Unable to load API keys.');
        });
    }

    function deleteAPIKey(key) {
        Axios.request({ 
            method: 'delete', 
            url: baseurl + api['api_key_remove'], 
            headers: { Authorization: 'Bearer ' + Auth.token},
            params: {'key': key}
        })
        .then((response) => {
            getAPIKeys(); // Reload all API keys
        }, (error) => {
            console.log('Unable to remove API key.');
        });
    }

    function createAPIKey() {
        Axios.request({ 
            method: 'post', 
            url: baseurl + api['api_key_new'], 
            headers: { Authorization: 'Bearer ' + Auth.token},
            params: {
                'key_owner_username': Auth.getUsername(),
                'service': newKeyType,
                'detail': newKeyDetail,
            }
        })
        .then((response) => {
            getAPIKeys(); // Reload all API keys
            setNewKeyDialogOpen(false);
            setSuccessSnackbarMessage('Successfully generated API key.');
            setSuccessSnackbarOpen(true);
        }, (error) => {
            console.log('Unable to create API key.');
        });
    }

    // Set image total from localstorage

    return (
        <div className={classes.root}>
            <Box display={{ xs: 'none', sm: 'block' }} className={classes.loginTopPadding} xs={12}>

            </Box>

            <Grid
                container
                direction="row"
                spacing={3}
                display="flex"
                justify="center"
            >

                <Grid item xs={12} md={6}>
                    {(Auth.getRoles().includes('admin') || Auth.getRoles().includes('researcher')) &&
                        <Card className={classes.apiKeyListContainer}>
                        <CardContent>
                        <Grid justify="space-between" container>
                            
                            <Grid item>
                                <Typography variant="h5" style={{ marginBottom: '1em' }}> API Keys </Typography>
                            </Grid>
                            
                            <Grid item>
                                <Button
                                    variant="outlined" 
                                    size='small'
                                    disableElevation
                                    startIcon={<AddIcon />}
                                    onClick={() => setNewKeyDialogOpen(true)}
                                >
                                    Generate Key
                                </Button>
                            </Grid>
                        </Grid>


                     

                            <TableContainer className={classes.apiKeyListTable}>
                                <Table stickyHeader aria-label="sticky table">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Description</TableCell>
                                            <TableCell>Service</TableCell>
                                            <TableCell>Action</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {apiKeys.map((apiKeyObject) => (
                                            <TableRow key={apiKeyObject['key']}>
                                                <TableCell component="th" scope="row">
                                                    {apiKeyObject['detail']}
                                                </TableCell>
                                                <TableCell>
                                                    {apiKeyObject['type'].replaceAll('_', ' ')}
                                                </TableCell>
                                                <TableCell>
                                                    <ButtonGroup>
                                                        <Button
                                                            variant="contained" 
                                                            color="secondary"
                                                            onClick={() => {
                                                                navigator.clipboard.writeText(apiKeyObject['key']);
                                                                setSuccessSnackbarMessage('API Key Copied to Clipboard!');
                                                                setSuccessSnackbarOpen(true);
                                                            }}
                                                        >
                                                            Copy Key
                                                        </Button>
                                                        <Button
                                                            variant="contained" 
                                                            color="primary"
                                                            onClick={() => deleteAPIKey(apiKeyObject['key'])}
                                                        >
                                                            Delete
                                                        </Button>
                                                    </ButtonGroup>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </CardContent>
                    </Card>
                    }
                </Grid>

                <Grid item xs={12} md={6} className={classes.loginGrid2}>

                </Grid>
                <Grid item xs={12} md={6} className={classes.loginGrid1}>

                </Grid>

            </Grid>


            {/* Generate API Key Popup Dialog */}
            <Dialog open={newKeyDialogOpen} onClose={() => setNewKeyDialogOpen(false)} aria-labelledby="form-dialog-title">
                <DialogTitle id="form-dialog-title">Generate New API Key</DialogTitle>
                <DialogContent>
                <DialogContentText>
                    To generate a new API key, provide a brief description and the service it will be connected to.
                </DialogContentText>
                <TextField
                    autoFocus
                    label="API Key Description"
                    type="text"
                    onChange={(e) => setNewKeyDetail(e.target.value)}
                    fullWidth={true}
                />

                <TextField
                    id="standard-select-currency-native"
                    select
                    fullWidth={true}
                    value={newKeyType}
                    onChange={(e) => setNewKeyType(e.target.value)}
                    style={{marginTop: '1em'}}
                    helperText="Please Select Microservice"
                >
                    <MenuItem key='predict' value={'predict_microservice'}>
                        Prediction
                    </MenuItem>
                    <MenuItem key='train' value={'train_microservice'}>
                        Dataset and Training
                    </MenuItem>
                </TextField>
                </DialogContent>
                <DialogActions>
                <Button onClick={() => setNewKeyDialogOpen(false)} color="primary">
                    Cancel
                </Button>
                <Button onClick={() => createAPIKey()} color="secondary">
                    Submit
                </Button>
                </DialogActions>
            </Dialog>


            <Snackbar 
                open={successSnackbarOpen} 
                autoHideDuration={6000} 
                onClose={(e, r) => {if (r !== 'clickaway') setSuccessSnackbarOpen(false) }} 
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            >
                    <Alert onClose={() => setSuccessSnackbarOpen(false)} severity="success">
                        <Typography variant="h5" component="h4">{successSnackbarMessage}</Typography>
                    </Alert>
            </Snackbar>
        </div>
    );
};

export default Home;
