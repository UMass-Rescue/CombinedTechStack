const { dialog } = require('electron');

async function getFileFromUser () {
  const files = await dialog.showOpenDialog({
      title : "Data File",
      properties: ['openFile'],
      defaultPath: '~/'
    });

  if (!files) { return ''; }
  return(files.filePaths[0])
};


async function getFolderFromUser () {
  const files = await dialog.showOpenDialog({
      title : "Data Folder",
      properties: ['openDirectory'],
      defaultPath: '~/'
    });

  if (!files) { return ''; }
  return(files.filePaths[0])
};

module.exports =  {
  getFileFromUser,
  getFolderFromUser
}
