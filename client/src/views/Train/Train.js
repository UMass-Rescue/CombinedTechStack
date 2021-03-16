import React, {useEffect, useState} from 'react';
import {makeStyles} from '@material-ui/styles';
import {
    Accordion,
    AccordionActions, AccordionDetails, AccordionSummary,
    Button,
    Card,
    CardContent,
    Divider,
    Grid,
    Step,
    StepLabel,
    Stepper, Tab, Tabs, TextField
} from '@material-ui/core';
import Typography from "@material-ui/core/Typography";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";
import axios from "axios";
import {api, Auth, baseurl} from "../../api";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import TableCell from "@material-ui/core/TableCell";
import TableBody from "@material-ui/core/TableBody";
import Table from "@material-ui/core/Table";
import FileSaver from 'file-saver';

const useStyles = makeStyles(theme => ({
    root: {
        padding: theme.spacing(4),
        // overflowX: 'hidden',
    },
    expandedInfoCard: {
        marginBottom: 0,
        paddingBottom: 0
    }
}));


const Train = () => {
    const classes = useStyles();

    // Track Pending + Completed Jobs
    const [pending, setPending] = React.useState(-1);
    const [finished, setFinished] = React.useState(-1);

    // Training Info For Tab-View
    const [recent, setRecent] = React.useState([]);
    const [jobSearchField, setJobSearchField] = useState('');
    const [searchedJob, setSearchedJob] = React.useState({});

    const [activeStep, setActiveStep] = React.useState(0);
    const [currentTab, setCurrentTab] = React.useState(0);

    // This will run initially on page load
    useEffect(() => {
        // Load Statistics
        axios.request({
            method: 'get',
            url: baseurl + api['training_statistics'],
            headers: {Authorization: 'Bearer ' + Auth.token}
        }).then((response) => {
            setPending(response.data['pending'])
            setFinished(response.data['finished'])
        }, (error) => {

        });

        axios.request({
            method: 'get',
            url: baseurl + api['all_training_results'],
            params: {'limit': 8},
            headers: {Authorization: 'Bearer ' + Auth.token}
        }).then((response) => {
            setRecent(response.data['jobs'])
        }, (error) => {

        });
    }, []);


    const steps = [
        'Create Tensorflow2 Model',
        'Send to Remote Dataset',
        'View Training Results'
    ];

    function getStepContent(stepIndex) {
        switch (stepIndex) {
            case 0:
                return (
                    <Typography variant='subtitle1' component='p'>
                        Create a model using <a target='_blank' rel='noreferrer'
                                                href='https://www.tensorflow.org/api_docs/python/tf/keras/Model'>Keras
                        in Tensorflow</a>. Once the
                        structure of the model has been created, it is extremely simply to send it to the server for
                        training.
                    </Typography>
                )
            case 1:
                return (
                    <Typography variant='subtitle1' component='p'>
                        Using the <a target='_blank' rel='noreferrer' href='https://pypi.org/project/CitadelML/'>CitadelML Python
                        Library</a>, call
                        upload_model(), and then provide the model and desired hyperparameters. You will be given a
                        unique ID to track
                        the status of your training request
                    </Typography>
                )
            case 2:
                return (
                    <Typography variant='subtitle1' component='p'>
                        View training status and metrics on this page by ID.
                    </Typography>
                )
            default:
                return (
                    <Typography variant='subtitle1' component='p' color='primary'>
                        Error Loading Content.
                    </Typography>
                )
        }
    }


    function searchJob() {
        axios.request({
            method: 'get',
            url: baseurl + api['training_result'],
            params: {training_id: jobSearchField},
            headers: {Authorization: 'Bearer ' + Auth.token}
        }).then((response) => {
            setSearchedJob(response.data);
        }, (error) => {
            setSearchedJob({});
        });
    }

    function downloadJobs() {
        axios.request({
            method: 'get',
            url: baseurl + api['all_training_results'],
            headers: {Authorization: 'Bearer ' + Auth.token}
        }).then((response) => {
            let rows = response.data['jobs'];
            let csvData = 'Training ID,Dataset,Training Status,Training Accuracy,Validation Accuracy,Training Loss,Validation Loss\n';

            rows.forEach((tr) => {
                if (tr['complete']) {
                    if (tr['training_accuracy'] !== -1) { // If complete and not -1, then success
                        csvData += tr['training_id'] + ',' + tr['dataset'] + ',Complete,'
                            + tr['training_accuracy'] + ',' + tr['validation_accuracy'] + ','
                            + tr['training_loss'] + ',' + tr['validation_loss'] + '\n'
                    } else { // If complete and accuracy is -1, then there was an error training
                        csvData += tr['training_id'] + ',' + tr['dataset'] + ',Errored\n'
                    }

                } else {
                    csvData += tr['training_id'] + ',' + tr['dataset'] + ',Pending\n'
                }
            })

            let blob = new Blob([csvData], { type: "text/csv;charset=utf-8" });
            FileSaver.saveAs(blob, "Training Results.csv");

        }, (error) => {

        });
    }

    function downloadTrainedModel(training_id) {
        console.log('Downloading');
        axios.request({
            method: 'get',
            url: baseurl + api['download_trained_model'],
            headers: {Authorization: 'Bearer ' + Auth.token},
            params: {training_id: training_id},
            responseType: "blob"
        }).then((response) => {
            console.log('Response');
            let blob = new Blob([response.data], { type: 'application/octet-stream' })
            FileSaver.saveAs(blob, "Trained Model "+training_id+".zip");
        }, (error) => {
            console.log(error);
        });
    }


    return (
        <div className={classes.root}>
            <Grid
                container
                spacing={4}
                direction="row"
            >
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Grid container justify="space-between">
                                <Grid item xs={11}>
                                    <Typography gutterBottom variant="h4" component="h2">
                                        Pending Jobs
                                    </Typography>
                                </Grid>
                                <Grid item xs={1}>
                                    <Typography gutterBottom variant="h2" component="h2"
                                                color={pending === -1 ? 'primary' : 'inherit'}>
                                        {pending}
                                    </Typography>
                                </Grid>
                            </Grid>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Grid container justify="space-between">
                                <Grid item xs={11}>
                                    <Typography gutterBottom variant="h4" component="h2">
                                        Completed Jobs
                                    </Typography>
                                </Grid>
                                <Grid item xs={1} >
                                    <Typography gutterBottom variant="h2" component="h2"
                                                color={finished === -1 ? 'primary' : 'inherit'}>
                                        {finished}
                                    </Typography>
                                </Grid>
                            </Grid>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12}>

                    <Accordion
                        classes={{
                            expanded: classes.expandedInfoCard, // class name, e.g. `classes-nesting-root-x`
                        }}
                    >
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon/>}
                            aria-controls="panel1c-content"
                            id="panel1c-header"
                        >

                            <Typography variant='h5' component='h5'>Train a New Model</Typography>

                        </AccordionSummary>
                        <AccordionDetails>
                            <Grid container direction='row'>
                                <Grid item xs={12}>
                                    <Stepper activeStep={activeStep} alternativeLabel>
                                        {steps.map((label) => (
                                            <Step key={label}>
                                                <StepLabel>{label}</StepLabel>
                                            </Step>
                                        ))}
                                    </Stepper>
                                </Grid>

                                <Grid item xs={12}>
                                    <Typography paragraph align='center' variant="subtitle1" component="h5">
                                        {getStepContent(activeStep)}
                                    </Typography>
                                </Grid>
                            </Grid>
                        </AccordionDetails>
                        <Divider/>
                        <AccordionActions>
                            <Button
                                size="medium" color="primary"
                                disabled={activeStep === 0}
                                onClick={() => setActiveStep((prevActiveStep) => prevActiveStep - 1)}
                            >
                                Last Step
                            </Button>
                            <Button
                                size="medium" color="primary"
                                disabled={activeStep === 2}
                                onClick={() => setActiveStep((prevActiveStep) => prevActiveStep + 1)}
                            >
                                Next Step
                            </Button>
                        </AccordionActions>
                    </Accordion>
                </Grid>

                <Grid item xs={12}>
                    <Card>
                        <CardContent>
                            <Typography gutterBottom variant="h5" component="h2">
                                View Training Results
                            </Typography>
                            <Tabs
                                value={currentTab}
                                onChange={(e, newVal) => setCurrentTab(newVal)}
                                indicatorColor="primary"
                                textColor="primary"
                                centered
                            >
                                <Tab label="Recent" id='tab1'/>
                                <Tab label="By ID" id='tab2'/>
                                <Tab label="Export" id='tab3'/>
                            </Tabs>

                            <Divider style={{marginTop: '1em'}}/>

                            {/*Recent Jobs Panel*/}
                            {currentTab === 0 &&
                            <Table stickyHeader aria-label="sticky table">
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Training ID</TableCell>
                                        <TableCell>Dataset</TableCell>
                                        <TableCell>Status</TableCell>
                                        <TableCell>Training Accuracy</TableCell>
                                        <TableCell>Validation Accuracy</TableCell>
                                        <TableCell>Training Loss</TableCell>
                                        <TableCell>Validation Loss</TableCell>
                                        {Auth.getRoles().includes('admin') &&
                                            <TableCell>Trained Model</TableCell>
                                        }
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {recent.map((trainingObject) => (
                                        <TableRow key={trainingObject['training_id']}>
                                            <TableCell component="th" scope="row">
                                                {trainingObject['training_id']}
                                            </TableCell>
                                            <TableCell component="th" scope="row">
                                                {trainingObject['dataset'].replaceAll('_', ' ')}
                                            </TableCell>
                                            <TableCell>
                                                {trainingObject['complete'] ?
                                                    trainingObject['training_accuracy'] !== -1 ?
                                                        <Typography variant={'body1'} component={'p'}>
                                                            Finished
                                                        </Typography>
                                                    :
                                                        <Typography variant={'body1'} component={'p'} color='primary'>
                                                            Errored
                                                        </Typography>

                                                    :
                                                    <Typography variant={'body1'} component={'p'} color='secondary'>
                                                        Pending
                                                    </Typography>
                                                }
                                            </TableCell>
                                            <TableCell>
                                                {trainingObject['complete'] ?
                                                    <Typography variant={'body1'} component={'p'}>
                                                        {trainingObject['training_accuracy'].toFixed(4)}
                                                    </Typography>
                                                    :
                                                    <Typography variant={'body1'} component={'p'}>
                                                        ...
                                                    </Typography>
                                                }
                                            </TableCell>
                                            <TableCell>
                                                {trainingObject['complete'] ?
                                                    <Typography variant={'body1'} component={'p'}>
                                                        {trainingObject['validation_accuracy'].toFixed(4)}
                                                    </Typography>
                                                    :
                                                    <Typography variant={'body1'} component={'p'}>
                                                        ...
                                                    </Typography>
                                                }
                                            </TableCell>
                                            <TableCell>
                                                {trainingObject['complete'] ?
                                                    <Typography variant={'body1'} component={'p'}>
                                                        {trainingObject['training_loss'].toFixed(4)}
                                                    </Typography>
                                                    :
                                                    <Typography variant={'body1'} component={'p'}>
                                                        ...
                                                    </Typography>
                                                }
                                            </TableCell>
                                            <TableCell>
                                                {trainingObject['complete'] ?
                                                    <Typography variant={'body1'} component={'p'}>
                                                        {trainingObject['validation_loss'].toFixed(4)}
                                                    </Typography>
                                                    :
                                                    <Typography variant={'body1'} component={'p'}>
                                                        ...
                                                    </Typography>
                                                }
                                            </TableCell>
                                            {Auth.getRoles().includes('admin') &&
                                            <TableCell>
                                                {trainingObject['save'] ?
                                                    (trainingObject['complete'] ?
                                                            <Button color='secondary' variant='contained' size='small'
                                                                    onClick={() => downloadTrainedModel(trainingObject['training_id'])}>
                                                                Download
                                                            </Button>
                                                            :
                                                            <Button color='secondary' variant='contained' size='small'
                                                                    disabled>
                                                                Download
                                                            </Button>
                                                    )
                                                    :
                                                    <Typography variant={'body1'} component={'p'}>
                                                        Not Saved
                                                    </Typography>
                                                }
                                            </TableCell>
                                            }
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                            }

                            {/*Search By ID Panel*/}
                            {currentTab === 1 &&
                            <Grid container spacing={3} justify="center" alignItems="center" style={{marginTop: '1em'}}>
                                <Grid item xs={5}>
                                    <TextField
                                        fullWidth id="standard-basic"
                                        label="Training ID"
                                        onChange={(e) => setJobSearchField(e.target.value)}
                                        defaultValue={jobSearchField}
                                    />
                                </Grid>
                                <Grid item xs={1}>
                                    <Button color='secondary' size='medium' variant='contained' disableElevation
                                            onClick={searchJob}>Search</Button>
                                </Grid>

                                <Grid item xs={12}>
                                    <Divider/>
                                </Grid>

                                {Object.keys(searchedJob).length > 0 && searchedJob['status'] === 'success' &&

                                <Grid item xs={6}>
                                    <Grid container justify='space-between'>
                                        <Grid item xs={5}>
                                            <Typography gutterBottom variant="h5" component="h2">
                                                Dataset
                                            </Typography>
                                        </Grid>
                                        <Grid item xs={7}>
                                            <Typography gutterBottom variant="body1" component="p">
                                                {searchedJob['dataset']}
                                            </Typography>
                                        </Grid>

                                        <Grid item xs={5}>
                                            <Typography gutterBottom variant="h5" component="h2">
                                                Job Status
                                            </Typography>
                                        </Grid>
                                        <Grid item xs={7}>
                                            {searchedJob['complete'] ?
                                                searchedJob['training_accuracy'] !== -1 ?
                                                    <Typography variant={'body1'} component={'p'}>
                                                        Finished
                                                    </Typography>
                                                    :
                                                    <Typography variant={'body1'} component={'p'} color='primary'>
                                                        Errored
                                                    </Typography>

                                                :
                                                <Typography variant={'body1'} component={'p'} color='secondary'>
                                                    Pending
                                                </Typography>
                                            }
                                        </Grid>

                                        <Grid item xs={5}>
                                            <Typography gutterBottom variant="h5" component="h2">
                                                Training Accuracy
                                            </Typography>
                                        </Grid>
                                        <Grid item xs={7}>
                                            <Typography variant={'body1'} component={'p'}>
                                            {searchedJob['complete'] ?
                                                searchedJob['training_accuracy'].toFixed(4) : '...'
                                            }
                                            </Typography>
                                        </Grid>

                                        <Grid item xs={5}>
                                            <Typography gutterBottom variant="h5" component="h2">
                                                Validation Accuracy
                                            </Typography>
                                        </Grid>
                                        <Grid item xs={7}>
                                            <Typography variant={'body1'} component={'p'}>
                                                {searchedJob['complete'] ?
                                                    searchedJob['validation_accuracy'].toFixed(4) : '...'
                                                }
                                            </Typography>
                                        </Grid>

                                        <Grid item xs={5}>
                                            <Typography gutterBottom variant="h5" component="h2">
                                                Training Loss
                                            </Typography>
                                        </Grid>
                                        <Grid item xs={7}>
                                            <Typography variant={'body1'} component={'p'}>
                                                {searchedJob['complete'] ?
                                                    searchedJob['training_loss'].toFixed(4) : '...'
                                                }
                                            </Typography>
                                        </Grid>

                                        <Grid item xs={5}>
                                            <Typography gutterBottom variant="h5" component="h2">
                                                Validation Loss
                                            </Typography>
                                        </Grid>
                                        <Grid item xs={7}>
                                            <Typography variant={'body1'} component={'p'}>
                                                {searchedJob['complete'] ?
                                                    searchedJob['validation_loss'].toFixed(4) : '...'
                                                }
                                            </Typography>
                                        </Grid>

                                        {Auth.getRoles().includes('admin') &&
                                        <Grid item xs={5}>
                                            <Typography gutterBottom variant="h5" component="h2">
                                                Trained Model Files
                                            </Typography>
                                        </Grid>
                                        }

                                        {Auth.getRoles().includes('admin') &&
                                        <Grid item xs={7}>
                                            {searchedJob['save'] ?
                                                (searchedJob['complete'] ?
                                                    <Button color='secondary' variant='contained' size='small'
                                                            onClick={() => downloadTrainedModel(searchedJob['training_id'])}>
                                                        Download
                                                    </Button>
                                                    :
                                                    <Button color='secondary' variant='contained' size='small'
                                                            disabled>
                                                        Download
                                                    </Button>
                                                )
                                                :
                                                <Typography variant={'body1'} component={'p'}>
                                                    Not Saved
                                                </Typography>
                                            }
                                        </Grid>
                                        }


                                    </Grid>
                                </Grid>
                                }
                                {Object.keys(searchedJob).length > 0 && searchedJob['status'] !== 'success' &&
                                <Grid item xs={6}>
                                    <Typography variant='h4' component='h4' color='primary' align='center'>
                                        Unable to find job with specified training ID.
                                    </Typography>
                                </Grid>
                                }

                            </Grid>

                            }

                            {/*Export Panel*/}
                            {currentTab === 2 &&
                            <div>
                                <Grid container spacing={3} justify="center" alignItems="center" style={{marginTop: '1em'}}>
                                    <Grid item xs={3}>
                                        <Typography variant={'h4'} component={'h4'}>
                                            Export Training Results to CSV
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={2}>
                                        <Button
                                            variant='contained'
                                            fullWidth
                                            onClick={downloadJobs}
                                            color='primary'
                                            size='medium'
                                        >
                                            Download
                                        </Button>
                                    </Grid>
                                </Grid>
                            </div>
                            }
                        </CardContent>
                    </Card>
                </Grid>

            </Grid>
        </div>
    );
};

export default Train;
