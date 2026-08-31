/**
 * Upload a local file to a presigned PUT URL using XMLHttpRequest so we get
 * upload progress. This is compatible with the backend's signed-upload flow
 * (S3 presigned PUT URLs; local dev storage is a documented backend gap).
 */
export interface UploadProgress {
  loaded: number;
  total: number;
}

export function uploadFileToUrl(
  localUri: string,
  mimeType: string,
  uploadUrl: string,
  onProgress?: (progress: UploadProgress) => void,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', uploadUrl);

    if (onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          onProgress({ loaded: event.loaded, total: event.total });
        }
      };
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(new Error(`Upload failed with status ${xhr.status}`));
      }
    };
    xhr.onerror = () => reject(new Error('Upload failed: network error'));
    xhr.ontimeout = () => reject(new Error('Upload timed out'));

    // Read the local file as a blob and PUT it.
    const fileReader = new XMLHttpRequest();
    fileReader.open('GET', localUri);
    fileReader.responseType = 'blob';
    fileReader.onload = () => {
      const blob = fileReader.response as Blob;
      xhr.setRequestHeader('Content-Type', mimeType);
      xhr.send(blob);
    };
    fileReader.onerror = () => reject(new Error('Could not read the selected image'));
    fileReader.send();
  });
}
