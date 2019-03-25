from config import Config
from gcn_regression import GcnRegression
from gcn_classification import GcnClassification
from gmmconv_classification import GmmConvClassification
from gmmconv_classification_2_hidden_layers import GmmConvClassification2

from random_graph_dataset import RandomGraphDataset
from my_graph import MyGraph

import torch
import os
from torch_geometric.data import DataLoader


if __name__  == '__main__':
    config = Config().parse_args()

    # make necessary directory structure
    if not os.path.isdir(config.temp_dir):
        os.makedirs(config.temp_dir)

    # create and load dataset
    dataset = RandomGraphDataset(root=config.dataset_path, config=config)
    config.max_neighbors = dataset.max_neighbors()
    dataset = dataset.shuffle()

    # split into train and test
    split_index = int(config.samples * 0.8)
    train_dataset = dataset[:split_index]
    test_dataset = dataset[split_index:]

    data_loader = DataLoader(train_dataset, batch_size=1, shuffle=True)
    device = torch.device('cpu')

    try:
        model = globals()[config.model](config=config)
    except:
        raise NotImplementedError('The model you have specified is not implemented')
    model = model.to(device)


    # put model in training mode (e.g. use dropout)
    model.train()

    # TODO introduce support for minibatches > 1
    # TODO monitor validation loss during training
    for epoch in range(config.training_epochs):
        for data in data_loader:
            data = data.to(device)
            # clear the gradient variables of the model
            model.optimizer.zero_grad()
            # call the forward method
            out = model(data)
            loss = model.loss(out, data.y)
            model.print_current_loss(epoch)
            loss.backward()
            model.optimizer.step()

    # TODO introduce support for minibatches > 1 also for eval phase
    test_dataloader = DataLoader(test_dataset, batch_size=1, shuffle=False)
    eval_loss_values = []
    eval_metric_values = []

    for i, data in enumerate(test_dataloader):
        data = data.to(device)
        eval_loss_values.append(model.evaluate(data, i))
        eval_metric_values.append(model.evaluate_metric(data))

    print('')
    print('Maximum # of neighbors within distance {} in dataset: {}'.format(config.theta, config.max_neighbors))
    print('Mean test loss: {}'.format(
        torch.mean(torch.tensor(eval_loss_values))))
    print('Mean accuracy on test set: {}'.format(
        torch.mean(torch.tensor(eval_metric_values))))
    print('')

    # plot the first graph in the dataset
    g = MyGraph(config, dataset[0])
    g.plot_predictions(model.evaluate_as_list(data))
