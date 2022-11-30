# -*- coding: utf-8 -*-
"""Training_&_Testing SemiInfNet + MulticlassUNet.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1bmII5H1AHL4MQDGr6vsOCDi-BFtD_j1m

**Pooyan Rezaeipour Lasaki**

e-mails:
rezaeipourpooyan@gmail.com &
pooyan_rezaeipour@elec.iust.ac.ir

**Mohsen Safaei**

e-mails: mfsafaei78@gmail.com & mo_safaei@elec.iust.ac.ir

**Saeed Chamani**

e-mails: saeed.chamani10@gmail.com
& saeed_chamani@elec.iust.ac.ir

*Biomedical Engineering Department, School of Electrical Engineering, "Iran University of Science and Technology", Tehran*

*To find the files which you have uploaded in your "Google Drive"*
"""

from google.colab import drive
drive.mount('/content/gdrive')

"""*Unzipping the mentioned file which is named "Inf-Net-master"*"""

!unzip "/content/gdrive/MyDrive/Inf-Net-master.zip"

"""*For recognizing the module named "Code"*"""

cd '/content/Inf-Net-master'

import sys
sys.path.append('/content/Inf-Net-master')

"""*Training  "MyTrain_MulClsLungInf_UNet"   for Semi-Inf-Net + Multi-class UNet*

**Note** that if you run this file uninterruptedly after Semi-Inf-net(second method), you do not face a problem because the folder named "Snapshots" was created automatically.

 But for running this file seperately(which we do below), you must create a folder in "Snapshots" which is named "save_weights",then create a folder in "save_weights" which is named "{}".

Also change the last line which is " save_path='Semi-Inf-Net_UNet' " to " save_path='{}' "
"""

# -*- coding: utf-8 -*-

"""Preview
Code for 'Inf-Net: Automatic COVID-19 Lung Infection Segmentation from CT Scans'
submit to Transactions on Medical Imaging, 2020.

First Version: Created on 2020-05-13 (@author: Ge-Peng Ji)
"""

import os
import numpy as np
import torch.optim as optim
from Code.utils.dataloader_MulClsLungInf_UNet import LungDataset
from torchvision import transforms
# from LungData import test_dataloader, train_dataloader  # pls change batch_size
from torch.utils.data import DataLoader
from Code.model_lung_infection.InfNet_UNet import *


def train(epo_num, num_classes, input_channels, batch_size, lr, save_path):
    train_dataset = LungDataset(
        imgs_path='./Dataset/COVID-SemiSeg/Dataset/TrainingSet/MultiClassInfection-Train/Imgs/',
        # NOTES: prior is borrowed from the object-level label of train split
        pseudo_path='./Dataset/COVID-SemiSeg/Dataset/TrainingSet/MultiClassInfection-Train/Prior/',
        label_path='./Dataset/COVID-SemiSeg/Dataset/TrainingSet/MultiClassInfection-Train/GT/',
        transform=transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])]))
    train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    lung_model = Inf_Net_UNet(input_channels, num_classes)  # input_channels=3， n_class=3
    print(lung_model)
    lung_model = lung_model.to(device)

    criterion = nn.BCELoss().to(device)
    optimizer = optim.SGD(lung_model.parameters(), lr=lr, momentum=0.7)

    print("#" * 20, "\nStart Training (Inf-Net)\nThis code is written for 'Inf-Net: Automatic COVID-19 Lung "
                    "Infection Segmentation from CT Scans', 2020, TMI.\n"
                    "----\nPlease cite the paper if you use this code and dataset. "
                    "And any questions feel free to contact me "
                    "via E-mail (gepengai.ji@gmail.com)\n----\n", "#" * 20)

    for epo in range(epo_num):

        train_loss = 0
        lung_model.train()

        for index, (img, pseudo, img_mask, _) in enumerate(train_dataloader):

            img = img.to(device)
            pseudo = pseudo.to(device)
            img_mask = img_mask.to(device)

            optimizer.zero_grad()
            output = lung_model(torch.cat((img, pseudo), dim=1))

            output = torch.sigmoid(output)  # output.shape is torch.Size([4, 2, 160, 160])
            loss = criterion(output, img_mask)

            loss.backward()
            iter_loss = loss.item()
            train_loss += iter_loss
            optimizer.step()

            if np.mod(index, 20) == 0:
                print('Epoch: {}/{}, Step: {}/{}, Train loss is {}'.format(epo, epo_num, index, len(train_dataloader), iter_loss))

        os.makedirs('./checkpoints//UNet_Multi-Class-Semi', exist_ok=True)
        if np.mod(epo+1, 10) == 0:
            torch.save(lung_model.state_dict(),
                       './Snapshots/save_weights/{}/unet_model_{}.pkl'.format(save_path, epo+1))
            print('Saving checkpoints: unet_model_{}.pkl'.format(epo+1))


if __name__ == "__main__":
    train(epo_num=200,
          num_classes=3,
          input_channels=6,
          batch_size=16,
          lr=1e-2,
          save_path='{}')

"""*Testing "MyTest_MulClsLungInf_UNet"   for Semi-Inf-Net + Multi-class UNet*

For running this file seperately from second method(which we do below), change the one before the last line which is " snapshot_dir='./Snapshots/save_weights/Semi-Inf-Net_UNet/unet_model_200.pkl' " to  
 " snapshot_dir='./Snapshots/save_weights/{}/unet_model_200.pkl' "
"""

# -*- coding: utf-8 -*-

"""Preview
Code for 'Inf-Net: Automatic COVID-19 Lung Infection Segmentation from CT Scans'
submit to Transactions on Medical Imaging, 2020.

First Version: Created on 2020-05-13 (@author: Ge-Peng Ji)
"""

import os
import numpy as np
from Code.utils.dataloader_MulClsLungInf_UNet import LungDataset
from torchvision import transforms
from torch.utils.data import DataLoader
from Code.model_lung_infection.InfNet_UNet import *  # use U-Net for multi-class segmentation
from scipy import misc
from Code.utils.split_class import split_class
import shutil


def inference(num_classes, input_channels, snapshot_dir, save_path):
    test_dataset = LungDataset(
        imgs_path='./Dataset/COVID-SemiSeg/Dataset/TestingSet/MultiClassInfection-Test/Imgs/',
        pseudo_path='./Dataset/COVID-SemiSeg/Results/Lung infection segmentation/Semi-Inf-Net/',  # NOTES: generated from `Semi-Inf-Net`
        label_path='./Dataset/COVID-SemiSeg/Dataset/TestingSet/MultiClassInfection-Test/GT/',
        transform=transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                 std=[0.229, 0.224, 0.225])]),
        is_test=True
    )
    test_dataloader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    lung_model = Inf_Net_UNet(input_channels, num_classes).cuda()
    print(lung_model)
    lung_model.load_state_dict(torch.load(snapshot_dir))
    lung_model.eval()

    for index, (img, pseudo, img_mask, name) in enumerate(test_dataloader):
        img = img.to(device)
        pseudo = pseudo.to(device)
        img_mask = img_mask.to(device)

        output = lung_model(torch.cat((img, pseudo), dim=1))
        output = torch.sigmoid(output)  # output.shape is torch.Size([4, 2, 160, 160])
        b, _, w, h = output.size()
        _, _, w_gt, h_gt = img_mask.size()

        # output b*n_class*h*w -- > b*h*w
        pred = output.cpu().permute(0, 2, 3, 1).contiguous().view(-1, num_classes).max(1)[1].view(b, w, h).numpy().squeeze()
        print('Class numbers of prediction in total:', np.unique(pred))
        # pred = misc.imresize(pred, size=(w_gt, h_gt))
        os.makedirs(save_path, exist_ok=True)
        #misc.imsave(save_path + name[0].replace('.jpg', '.png'), pred)
        import imageio
        imageio.imwrite(save_path + name[0].replace('.jpg', '.png'), pred)
        split_class(save_path, name[0].replace('.jpg', '.png'), w_gt, h_gt)

    shutil.rmtree(save_path)
    print('Test done!')


if __name__ == "__main__":
    inference(num_classes=3,
              input_channels=6,
              snapshot_dir='./Snapshots/save_weights/{}/unet_model_200.pkl',
              save_path='./Results/Multi-class lung infection segmentation/class_12/'
              )