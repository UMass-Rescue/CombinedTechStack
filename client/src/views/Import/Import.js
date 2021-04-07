import React, { useState, useEffect } from 'react';
import { makeStyles } from '@material-ui/styles';
import axios from 'axios';
import {
    Grid,
    Typography,
    Button,
    Checkbox,
    FormControlLabel,
    CardContent,
    Box
} from '@material-ui/core';
import ImageDropzone from "../../components/ImageDropzone/ImageDropzone";
import Card from "@material-ui/core/Card";
import Table from "@material-ui/core/Table";
import TableRow from "@material-ui/core/TableRow";
import TableCell from "@material-ui/core/TableCell";
import TableBody from "@material-ui/core/TableBody";
import CheckCircleOutlineIcon from '@material-ui/icons/CheckCircleOutline';
import IconButton from '@material-ui/core/IconButton';
import DeleteIcon from '@material-ui/icons/Delete';
import TableHead from "@material-ui/core/TableHead";
import Snackbar from "@material-ui/core/Snackbar";
import Alert from "@material-ui/lab/Alert";
import TableContainer from "@material-ui/core/TableContainer";
import DoneAllIcon from '@material-ui/icons/DoneAll';
import ClearIcon from '@material-ui/icons/Clear';
import { api, Auth, baseurl } from 'api';

const useStyles = makeStyles(theme => ({
    root: {
        padding: theme.spacing(4)
    },
    modelSelectorCard: {
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: '1em',
        paddingBottom: '1em',
        paddingLeft: '10vw',
        paddingRight: '10vw',
        marginBottom: '1em',
    },
    modelSelectorContainer: {
        width: '100%',
        height: '55vh',
        borderRadius: '0.6em',
    },
    modelSelectorTable: {
        overflow: 'auto',
        maxHeight: '45vh',
    },
    imageListContainer: {
        width: '100%',
        height: '55vh',
        borderRadius: '0.6em',
    },
    imageListTable: {
        overflow: 'auto',
        maxHeight: '45vh',
    },
    uploadButtonContainer: {
        width: '100%',
        maxHeight: '55vh',
        borderRadius: '0.6em',
        paddingBottom: '3vh',
        paddingTop: '3vh'
    },
    headerGridCard: {
        width: '100%'
    }
}));

const Import = () => {
    const classes = useStyles();

    const [filesToUpload, setFilesToUpload] = useState([]); // Files to be uploaded to photoanalysisserver
    const [filesUploaded, setFilesUploaded] = useState([]); // Files successfully uploaded to server
    const [modelsAvailable, setModelsAvailable] = useState([]);  // Models available from the photoanalysisserver
    const [modelsToUse, setModelsToUse] = useState([]);  // Models for the photoanalysisserver to use on uploads
    const [open, setOpen] = useState(false); // Handles state of image upload snackbar
    const [allChecked, setAllChecked] = useState(false); // If all models are selected

    useEffect(() => {
        axios.request({
                method: 'get', 
                url: baseurl + api['model_predict_list'], 
                headers: { Authorization: 'Bearer ' + Auth.token } 
            }).then((response) => {
                setModelsAvailable(response.data['models']);
            }, (error) => {
                console.log('Unable to connect to server or no models available.');
            });
    }, []);


    function addFilesToUpload(files) {
        setFilesToUpload([...filesToUpload, ...files]);
    }


    function toggleAddModelToUse(modelName) {
        if (modelsToUse.indexOf(modelName) > -1) {
            let newModels = [...modelsToUse]
            newModels.splice(modelsToUse.indexOf(modelName), 1);
            setModelsToUse(newModels);
        } else {
            let newModels = [...modelsToUse]
            newModels.push(modelName);
            setModelsToUse(newModels);
        }
    }


    function uploadImages() {

        const requestURL = baseurl + api['model_predict'];
        let currIndex = 0;
        while (currIndex < filesToUpload.length) {

            // Upload images in batches of 3
            for (let imageCount = 0; imageCount < 3; imageCount++) {

                // Ensure we have an image to upload
                if (currIndex >= filesToUpload.length) {
                    break;
                }

                const formData = new FormData();
                let fileNames = [];
                let currPlus3 = currIndex + 3;
                for (currIndex; currIndex < currPlus3; currIndex++) {
                    if (currIndex >= filesToUpload.length) {
                        break;
                    }
                    formData.append('images', filesToUpload[currIndex]);
                    fileNames.push(filesToUpload[currIndex].name);
                }
                for (let i = 0; i < modelsToUse.length; i++) {
                    formData.append('models', modelsToUse[i]);
                }

                const config = {
                    'Authorization': 'Bearer ' + Auth.token,
                    'content-type': 'multipart/form-data'
                };
                axios.request({ url: requestURL, method: 'post', headers: config, data: formData }).then((response) => {
                    setOpen(true); // Display success message
                    setFilesUploaded(curr => [...curr, ...fileNames]);
                });
            }

        }
    }

    const handleSnackbarClose = (event, reason) => {
        if (reason === 'clickaway') {
            return;
        }

        setOpen(false);
    };

    function handleRemoveImage(filename) {
        const newList = filesToUpload.filter((item) => item.name !== filename);
        setFilesToUpload(newList);
    }

    return (
        <div className={classes.root}>

            <ImageDropzone filelistfunction={addFilesToUpload} />

            <div style={{ marginTop: '1em' }}>
                <Box display={{xs: 'none', md: 'block'}}>
                    <Grid
                        container
                        spacing={2}
                    >

                        {/*Header Card: Images*/}
                        <Grid item md={4}>
                            <Card className={classes.headerGridCard}>
                                <CardContent>
                                    <Typography variant="h3">
                                        1. Add Images
                                </Typography>
                                </CardContent>
                            </Card>
                        </Grid>

                        {/*Header Card: Models*/}
                        <Grid item md={4} >
                            <Card className={classes.headerGridCard}>
                                <CardContent>
                                    <Typography variant="h3">
                                        2. Choose Models
                                </Typography>
                                </CardContent>
                            </Card>
                        </Grid>

                        {/*Header Card: Upload*/}
                        <Grid item md={4} >
                            <Card className={classes.headerGridCard}>
                                <CardContent>
                                    <Typography variant="h3">
                                        3. Upload for Processing
                                </Typography>
                                </CardContent>
                            </Card>
                        </Grid>

                        </Grid>
                </Box>
                <Grid
                container
                spacing={2}
                display="flex"
                >

                    {/*Train Images*/}
                    <Grid item xs={12} md={4}>
                        <Card className={classes.imageListContainer}>
                            <CardContent>
                                <Typography variant="h5" style={{ marginBottom: '1em' }}>
                                    Images
                                </Typography>

                                <TableContainer className={classes.imageListTable}>
                                    <Table stickyHeader aria-label="sticky table">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>Filename</TableCell>
                                                <TableCell>Upload Status</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {filesToUpload.map((fileObject) => (
                                                <TableRow key={fileObject.name}>
                                                    <TableCell component="th" scope="row">
                                                        {fileObject.name}
                                                    </TableCell>
                                                    <TableCell style={{justifyContent: 'center'}}>
                                                        {(filesUploaded.includes(fileObject.name) &&
                                                            <IconButton aria-label="check"  size="small" disabled style={{color: 'green'}} className={classes.uploadedButton} >
                                                                <CheckCircleOutlineIcon />
                                                            </IconButton>
                                                        ) ||
                                                            <IconButton aria-label="delete"  size="small" onClick={() => { handleRemoveImage(fileObject.name) }}>
                                                              <DeleteIcon />
                                                            </IconButton>
                                                        }
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/*Select Models*/}
                    <Grid item xs={12} md={4}>
                        <Card className={classes.modelSelectorContainer}>
                            <CardContent>
                                <Grid justify="space-between" container>
                                    <Grid item>
                                        <Typography variant="h5" style={{ marginBottom: '1em' }}> Select Models </Typography>
                                    </Grid>

                                    <Grid item>
                                        {modelsAvailable.length > 0 ?
                                            <div id="model-select-button">
                                                {!allChecked ?
                                                    <Button
                                                        variant="outlined"
                                                        size='small'
                                                        type="button"
                                                        disableElevation
                                                        startIcon={<DoneAllIcon />}
                                                        onClick={() => {
                                                            setAllChecked(true);
                                                            setModelsToUse([...modelsAvailable]);
                                                        }}
                                                    >
                                                        Use All
                                                    </Button>
                                                    :
                                                    <Button
                                                        variant="outlined"
                                                        size='small'
                                                        type="button"
                                                        disableElevation
                                                        startIcon={<ClearIcon />}
                                                        onClick={() => {
                                                            setAllChecked(false);
                                                            setModelsToUse([]);
                                                        }}
                                                    >
                                                        Clear
                                                </Button>
                                                }
                                            </div>
                                            :
                                            <div id='no-model-select-button'></div>
                                        }
                                    </Grid>
                                </Grid>
                                <Table className={classes.modelSelectorTable} stickyHeader aria-label="sticky table">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Model</TableCell>
                                            <TableCell>Selected</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {modelsAvailable.map((modelName) => (
                                            <TableRow key={modelName}>
                                                <TableCell component="th" scope="row">
                                                    {modelName.replaceAll('_', ' ')}
                                                </TableCell>
                                                <TableCell>
                                                    {!allChecked ?
                                                        <FormControlLabel
                                                            id={modelName}
                                                            control={<Checkbox onChange={() => toggleAddModelToUse(modelName)} />}
                                                            label={''}
                                                        />
                                                        :
                                                        <CheckCircleOutlineIcon />
                                                    }
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>

                            </CardContent>
                        </Card >
                    </Grid>

                    {/* Upload Images*/}
                    <Grid item xs={12} md={4}>
                        <Card className={classes.uploadButtonContainer}>
                            <CardContent>
                                <Button
                                    variant="contained" color="primary" type="button"
                                    onClick={uploadImages} disabled={filesToUpload.length === 0 || modelsToUse.length === 0}
                                    style={{ marginLeft: '30%', width: '40%'}}
                                >
                                    Upload
                                </Button>
                            </CardContent>
                        </Card>
                    </Grid>


                </Grid>

                <Snackbar open={open} autoHideDuration={6000} onClose={handleSnackbarClose} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
                    <Alert onClose={handleSnackbarClose} severity="success">
                        <Typography variant="h5" component="h4">Images Successfully Uploaded</Typography>
                    </Alert>
                </Snackbar>

            </div>

        </div>
    );
};

export default Import;
