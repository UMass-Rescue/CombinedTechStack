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
    Box,
    Chip
} from '@material-ui/core';
import VideoDropzone from "../../components/VideoDropzone/VideoDropzone";
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
    videoListContainer: {
        width: '100%',
        height: '55vh',
        borderRadius: '0.6em',
    },
    videoListTable: {
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
    const [open, setOpen] = useState(false); // Handles state of video upload snackbar
    const [allChecked, setAllChecked] = useState(false); // If all models are selected
    const [modelsTags, setModelsTags] = useState({}); // Models tags from the photoanalysisserver

    useEffect(() => {
        axios.request({
                method: 'get', 
                url: baseurl + api['model_video_list'], 
                headers: { Authorization: 'Bearer ' + Auth.token } 
            }).then((response) => {
                setModelsAvailable(response.data['models']);
            }, (error) => {
                console.log('Unable to connect to server or no models available.');
            });
    }, []);

    /* This imports the model tags from the HTTP get and then divides the list by comma*/
    useEffect(() => {
        axios.request({
                method: 'get', 
                url: baseurl + api['model_tag_list'], 
                headers: { Authorization: 'Bearer ' + Auth.token } 
            }).then((response) => {
                // HTTP GET returns an array with the dictionary
                for (const tagItem in response.data['tags']) {
                    // Loop through all items in the dictionary, split the strings by comma into lists
                    response.data['tags'][tagItem] = response.data['tags'][tagItem].split(",");
                };
                setModelsTags(response.data['tags']);
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


    function uploadVideos() {

        const requestURL = baseurl + api['model_predict'];
        let currIndex = 0;
        while (currIndex < filesToUpload.length) {

            // Upload videos in batches of 3
            for (let videoCount = 0; videoCount < 3; videoCount++) {

                // Ensure we have an video to upload
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
                    formData.append('objects', filesToUpload[currIndex]);
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

    function handleRemoveVideo(filename) {
        const newList = filesToUpload.filter((item) => item.name !== filename);
        setFilesToUpload(newList);
    }

    return (
        <div className={classes.root}>

            <VideoDropzone filelistfunction={addFilesToUpload} />

            <div style={{ marginTop: '1em' }}>
                <Box display={{xs: 'none', md: 'block'}}>
                    <Grid
                        container
                        spacing={2}
                    >

                        {/*Header Card: Videos*/}
                        <Grid item md={4}>
                            <Card className={classes.headerGridCard}>
                                <CardContent>
                                    <Typography variant="h3">
                                        1. Add Videos
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

                    {/*Train Videos*/}
                    <Grid item xs={12} md={4}>
                        <Card className={classes.videoListContainer}>
                            <CardContent>
                                <Typography variant="h5" style={{ marginBottom: '1em' }}>
                                    Videos
                                </Typography>

                                <TableContainer className={classes.videoListTable}>
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
                                                            <IconButton aria-label="delete"  size="small" onClick={() => { handleRemoveVideo(fileObject.name) }}>
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
                                            <TableCell>Tags</TableCell>
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
                                                <TableCell>
                                                    {/*Find tags by modelname and print*/}
                                                    {modelsTags[modelName] && modelsTags[modelName].map((tags, index) => (
                                                        <Chip label = {tags} key={index}/>
                                                    ))}
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>

                            </CardContent>
                        </Card >
                    </Grid>

                    {/* Upload Videos*/}
                    <Grid item xs={12} md={4}>
                        <Card className={classes.uploadButtonContainer}>
                            <CardContent>
                                <Button
                                    variant="contained" color="primary" type="button"
                                    onClick={uploadVideos} disabled={filesToUpload.length === 0 || modelsToUse.length === 0}
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
                        <Typography variant="h5" component="h4">Videos Successfully Uploaded</Typography>
                    </Alert>
                </Snackbar>

            </div>

        </div>
    );
};

export default Import;
